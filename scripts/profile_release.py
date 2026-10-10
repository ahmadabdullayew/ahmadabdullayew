#!/usr/bin/env python3
"""Phase 6: deterministic profile-artifact handoff, guarded publication and verification.

No network I/O or git operations occur in 'bundle', 'inspect', or 'apply'.
Network/remote publication is deliberately confined to 'publish'/'verify-public'.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

from generate_contributions import OUTPUT_NAMES

ROOT = Path(__file__).resolve().parents[1]
OWNED = tuple(f"profile/{name}" for name in OUTPUT_NAMES)
MAX_BUNDLE_BYTES = 700_000
MAX_FILE_BYTES = 180_000
MAX_FRESH_HOURS = 6
CONTRACT_PATHS = (
    "README.md", "profile-spec.json", "scripts/generate_contributions.py",
    "scripts/validate_profile.py", ".github/workflows/update-contributions.yml",
    ".github/workflows/profile-quality.yml", "scripts/profile_release.py",
)
STAMP_RE = re.compile(r"\*\*Snapshot retrieved \(UTC\):\*\* (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)")
TOTAL_RE = re.compile(r"\*\*Reported contribution total:\*\* ([\d,]+)")
DATE_RE = re.compile(r"\*\*Reporting dates:\*\* (\d{4}-\d\d-\d\d) through (\d{4}-\d\d-\d\d)")


class ReleaseError(ValueError):
    """A release candidate does not meet the publication contract."""


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def decode_summary(raw: bytes, *, now: dt.datetime | None = None, fresh: bool = True) -> dict:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReleaseError("summary is not valid UTF-8") from exc
    stamp_match, total_match, dates = STAMP_RE.search(text), TOTAL_RE.search(text), DATE_RE.search(text)
    if not all((stamp_match, total_match, dates)):
        raise ReleaseError("summary lacks required date, total or explicit UTC retrieval provenance")
    try:
        capture = dt.datetime.strptime(stamp_match.group(1), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
        start, end = (dt.date.fromisoformat(dates.group(i)) for i in (1, 2))
    except ValueError as exc:
        raise ReleaseError("summary reports malformed dates") from exc
    current = now or utcnow()
    if current.tzinfo is None:
        raise ReleaseError("current time must be timezone-aware")
    age = (current.astimezone(dt.timezone.utc) - capture).total_seconds()
    if fresh and not (-300 <= age <= MAX_FRESH_HOURS * 3600):
        raise ReleaseError(f"candidate retrieval timestamp outside allowed {MAX_FRESH_HOURS}h window")
    if start > end or end > capture.date() + dt.timedelta(days=1):
        raise ReleaseError("summary reporting period inconsistent with retrieval date")
    total = int(total_match.group(1).replace(",", ""))
    if total < 0:
        raise ReleaseError("invalid negative total")
    monthly = re.findall(r'^\| (\d{4}-\d\d) \| (\d+) \| ', text, flags=re.M)
    daily = re.findall(r'^\| (\d{4}-\d\d-\d\d) \| (\d+) \|$', text, flags=re.M)
    if not monthly or not daily or sum(int(n) for _, n in daily) != total or sum(int(n) for _, n in monthly) != total:
        raise ReleaseError("summary day/month totals do not match stated total")
    if daily[0][0] != start.isoformat() or daily[-1][0] != end.isoformat():
        raise ReleaseError("summary first/last dates inconsistent with reporting dates")
    return {"retrieved_utc": stamp_match.group(1), "total": total,
            "period_start": str(start), "period_end": str(end)}


def verify_assets(files: dict[str, bytes], *, now: dt.datetime | None = None, fresh: bool = True) -> dict:
    if set(files) != set(OWNED):
        raise ReleaseError("candidate must contain exactly five registered owned assets")
    if any(not raw or len(raw) > MAX_FILE_BYTES for raw in files.values()):
        raise ReleaseError("asset missing, empty or larger than allowed limit")
    meta = decode_summary(files["profile/contributions-summary.md"], now=now, fresh=fresh)
    ns = '{http://www.w3.org/2000/svg}'
    for name in OWNED:
        if not name.endswith('.svg'):
            continue
        raw = files[name]
        try:
            tree = ET.fromstring(raw)
        except ET.ParseError as exc:
            raise ReleaseError(f"invalid SVG: {name}") from exc
        if tree.tag != ns+'svg' or tree.get('role') != 'img' or tree.get('aria-labelledby') != 'title desc':
            raise ReleaseError(f"invalid SVG root semantics: {name}")
        title, desc = tree.find(ns+'title'), tree.find(ns+'desc')
        if title is None or desc is None or not ''.join(title.itertext()).strip():
            raise ReleaseError(f"missing SVG alternative text: {name}")
        caption = ' '.join(desc.itertext())
        if meta['retrieved_utc'] not in caption or str(meta['total']) not in caption:
            raise ReleaseError(f"SVG provenance/count mismatch: {name}")
        if re.search(r'<\s*(?:animate|animateMotion|animateTransform|set)\b|@keyframes|animation\s*:',raw.decode('utf-8'),re.I):
            raise ReleaseError(f"motion forbidden in SVG: {name}")
    return meta


def pack(root: Path, output: Path, source_sha: str, *, now: dt.datetime | None = None) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ReleaseError("source must be an exact 40-character git commit SHA")
    files = {name:(root/name).read_bytes() for name in OWNED}
    meta = verify_assets(files,now=now)
    manifest = {"format": 1, "source_commit": source_sha, "snapshot": meta,
                "files": {name:{"sha256":sha(files[name]),"bytes":len(files[name])} for name in OWNED}}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json",json.dumps(manifest,sort_keys=True,indent=2).encode('utf-8')+b'\n')
        for name in OWNED:
            archive.writestr(name, files[name])
    print(f"PROFILE_RELEASE bundle validated: {output.name}; retrieved={meta['retrieved_utc']}; total={meta['total']}")
    return manifest


def inspect(bundle: Path, *, now: dt.datetime | None = None, fresh: bool = True) -> tuple[dict,dict[str, bytes]]:
    if not bundle.is_file() or bundle.stat().st_size > MAX_BUNDLE_BYTES:
        raise ReleaseError("bundle missing or exceeds configured size")
    try:
        with zipfile.ZipFile(bundle) as z:
            entries=z.infolist()
            if len(entries)!=len(OWNED)+1 or set(z.namelist()) != set(OWNED)|{'manifest.json'}:
                raise ReleaseError("bundle contains unexpected or missing paths")
            for item in entries:
                if item.is_dir() or item.file_size>MAX_FILE_BYTES or (item.external_attr >> 16)&0o170000==0o120000:
                    raise ReleaseError("bundle contains oversized, directory or symlink member")
            manifest=json.loads(z.read("manifest.json"))
            files={n:z.read(n) for n in OWNED}
    except (zipfile.BadZipFile,KeyError,UnicodeDecodeError,json.JSONDecodeError) as exc:
        raise ReleaseError("bundle is malformed") from exc
    if not isinstance(manifest,dict) or manifest.get('format')!=1 or not re.fullmatch(r'[0-9a-f]{40}',str(manifest.get('source_commit',''))):
        raise ReleaseError("invalid bundle manifest or source commit")
    if not isinstance(manifest.get('files'),dict) or set(manifest['files'])!=set(OWNED):
        raise ReleaseError("manifest has incomplete/unexpected asset inventory")
    for name,raw in files.items():
        if manifest['files'][name] != {"sha256":sha(raw),"bytes":len(raw)}:
            raise ReleaseError(f"bundle checksum or length mismatch: {name}")
    meta=verify_assets(files,now=now,fresh=fresh)
    if meta!=manifest.get('snapshot'):
        raise ReleaseError("bundle snapshot provenance does not match manifest")
    return manifest,files


def apply(bundle: Path, root: Path, *, now: dt.datetime | None = None) -> dict:
    """Verify all bytes first, then replace only the registered paths, restoring on normal failures."""
    manifest,files=inspect(bundle,now=now)
    root=root.resolve()
    directory=root/'profile'
    if not directory.is_dir() or directory.is_symlink():
        raise ReleaseError('profile directory missing or symlinked')
    originals={n:(root/n).read_bytes() if (root/n).exists() else None for n in OWNED}
    if any((root/n).is_symlink() for n in OWNED):
        raise ReleaseError('refusing symlink asset target')
    try:
        for n in OWNED:
            fd,tmp_name=tempfile.mkstemp(prefix='.phase6-new-',dir=directory)
            tmp=Path(tmp_name)
            try:
                with os.fdopen(fd,'wb') as fp:
                    fp.write(files[n])
                os.replace(tmp,root/n)
            finally:
                tmp.unlink(missing_ok=True)
    except BaseException:
        for n,raw in originals.items():
            if raw is None:
                (root/n).unlink(missing_ok=True)
            else:
                (root/n).write_bytes(raw)
        raise
    return manifest


def git(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(['git',*args],cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=check)


def validate_local(root: Path) -> None:
    commands=(['python3','-m','unittest','discover','-s','tests','-v'],
              ['python3','scripts/validate_profile.py'],
              ['python3','scripts/check_visuals.py'])
    for cmd in commands:
        proc=subprocess.run(cmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if proc.returncode:
            raise ReleaseError(f"prepublication check failed ({' '.join(cmd)}):\n{proc.stdout[-3500:]}")
        print('PASS prepublication:', ' '.join(cmd))


def changed_since(root:Path, candidate_sha:str) -> list[str]:
    out=git('diff','--name-only',candidate_sha,'HEAD','--',*OWNED,*CONTRACT_PATHS,cwd=root)
    return [p for p in out.stdout.splitlines() if p]


def prepare_against_latest(root:Path,bundle:Path,source_commit:str) -> tuple[str,bool]:
    git('fetch','--no-tags','origin','main',cwd=root)
    git('checkout','-B','phase6-publish','refs/remotes/origin/main',cwd=root)
    if git('merge-base','--is-ancestor',source_commit,'HEAD',cwd=root,check=False).returncode!=0:
        raise ReleaseError('candidate base is not an ancestor of current main; rerun generator')
    conflict=changed_since(root,source_commit)
    if conflict:
        raise ReleaseError(f'profile contract or owned assets changed since generation: {conflict}. Rerun generator')
    apply(bundle,root)
    validate_local(root)
    git('add','--',*OWNED,cwd=root)
    dirty=git('diff','--cached','--name-only',cwd=root).stdout.splitlines()
    if any(n not in OWNED for n in dirty):
        raise ReleaseError('unowned files unexpectedly staged')
    if not dirty:
        return git('rev-parse','HEAD',cwd=root).stdout.strip(),False
    git('-c','user.name=github-actions[bot]','-c','user.email=41898282+github-actions[bot]@users.noreply.github.com',
        'commit','-m','chore(profile): publish verified contribution snapshot',cwd=root)
    return git('rev-parse','HEAD',cwd=root).stdout.strip(),True


def note_result(status:str,sha_commit:str,details:str) -> None:
    output=os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output,'a',encoding='utf-8') as out:
            out.write(f"status={status}\ncommit_sha={sha_commit}\n")
    summary=os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a',encoding='utf-8') as out:
            out.write(f"### Contribution publication\n- Status: **{status}**\n- Commit: `{sha_commit}`\n- Details: {details}\n")
    print(f"PROFILE_PUBLICATION status={status} commit={sha_commit} {details}")


def create_fallback_pr(root:Path, sha_commit:str, run_id:str) -> None:
    if not re.fullmatch(r'\d{1,24}(?:-\d{1,4})?',run_id):
        raise ReleaseError('safe GITHUB_RUN_ID is required for PR fallback')
    branch=f'automation/profile-activity-{run_id}'
    git('push','origin',f'HEAD:refs/heads/{branch}',cwd=root)
    result=subprocess.run(['gh','pr','create','--base','main','--head',branch,
       '--title','chore(profile): update verified activity snapshot',
       '--body','Automated read-only generation and verified candidate; direct main push was rejected. Review required before merge. CI checks on bot-created PRs may need a manual workflow dispatch.'],
       cwd=root,text=True,capture_output=True)
    if result.returncode:
        raise ReleaseError('fallback branch pushed, but PR creation failed; open a PR manually for '+branch+': '+result.stderr[-400:])
    print('PR fallback created:',result.stdout.strip())


def publish(root:Path,bundle:Path,*,run_id:str, attempts:int=3) -> tuple[str,str]:
    manifest,_=inspect(bundle)
    source=manifest['source_commit']
    if not 1<=attempts<=4:
        raise ReleaseError('invalid retry count')
    for attempt in range(1,attempts+1):
        commit,updated=prepare_against_latest(root,bundle,source)
        if not updated:
            note_result('unchanged',commit,'The published assets already match the verified snapshot.')
            return 'unchanged',commit
        push=git('push','origin','HEAD:refs/heads/main',cwd=root,check=False)
        if push.returncode==0:
            note_result('direct-main',commit,'Fast-forward-only update; branch policy permitted direct publication.')
            return 'direct-main',commit
        # Detect a non-fast-forward race, instead of overwriting another writer's commit.
        try:
            git('fetch','--no-tags','origin','main',cwd=root)
            moved=git('merge-base','--is-ancestor','HEAD','refs/remotes/origin/main',cwd=root,check=False).returncode==0
            if moved:
                note_result('unchanged',commit,'Identical commit is already visible on main.')
                return 'unchanged',commit
            latest=git('rev-parse','refs/remotes/origin/main',cwd=root).stdout.strip()
            parent=git('rev-parse','HEAD^',cwd=root).stdout.strip()
            if latest!=parent and attempt<attempts:
                print(f'Non-fast-forward publication race, retrying latest main ({attempt}/{attempts})')
                continue
        except subprocess.CalledProcessError as exc:
            raise ReleaseError(f'cannot determine whether push failed safely: {exc.stderr}') from exc
        print('Direct main push rejected or unavailable; falling back to a reviewable pull request')
        create_fallback_pr(root,commit,run_id)
        note_result('pull-request',commit,'Protected-main or push restriction: review/merge pending; NOT published on main.')
        return 'pull-request',commit
    raise ReleaseError('publication race retry budget exhausted')


def check_public(username:str, sha_commit:str,*,opener=None, attempts:int=3, require_fresh:bool=False) -> None:
    """Verify public committed content + GitHub profile page, not assistive-tech behavior."""
    if not re.fullmatch(r'[a-zA-Z0-9-]{1,39}',username) or not re.fullmatch(r'[0-9a-f]{40}',sha_commit):
        raise ReleaseError('invalid public profile account or commit SHA')
    opener=opener or urllib.request.urlopen
    urls=[f'https://raw.githubusercontent.com/{username}/{username}/{sha_commit}/{path}'
          for path in ('README.md',*OWNED)]
    page=f'https://github.com/{username}'
    head_url=f'https://api.github.com/repos/{username}/{username}/commits/main'
    for attempt in range(attempts):
        try:
            with opener(urllib.request.Request(head_url,headers={'User-Agent':'profile-release-verifier','Accept':'application/vnd.github+json'}),timeout=15) as response:
                live_head=json.loads(response.read(250_000))
            if live_head.get('sha')!=sha_commit:
                raise ReleaseError('published main branch tip does not equal requested commit SHA')
            remote_files={}
            for path,url in zip(('README.md',*OWNED),urls):
                req=urllib.request.Request(url,headers={'User-Agent':'profile-release-verifier'})
                with opener(req,timeout=15) as response:
                    data=response.read(200_000)
                    if not data:
                        raise ReleaseError(f'empty public artifact {path}')
                if path in OWNED:
                    remote_files[path]=data
                if path=='README.md' and (b'Featured Projects' not in data or b'Bahar' not in data):
                    raise ReleaseError('public README lacks required project headings')
                if path.endswith('.svg'):
                    ET.fromstring(data)
                print('PUBLIC_OK',path)
            if require_fresh:
                verify_assets(remote_files,fresh=True)
                print('PUBLIC_OK five-asset snapshot consistency and UTC freshness')
            req=urllib.request.Request(page,headers={'User-Agent':'Mozilla/5.0 profile-publication-verifier'})
            with opener(req,timeout=15) as response:
                html=response.read(3_000_000).decode('utf-8',errors='replace')
            if not all(key in html for key in ('Bahar','ASANAppeal')):
                raise ReleaseError('public GitHub profile response lacks expected featured projects')
            print('PUBLIC_OK GitHub profile page (content presence; not a rendered-browser accessibility test)')
            return
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ReleaseError,ET.ParseError) as exc:
            if attempt+1==attempts:
                raise ReleaseError(f'public verification failed after {attempts} attempts: {exc}') from exc
            import time
            time.sleep(min((attempt+1)*3,9))


def main(argv:list[str]|None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('bundle');p.add_argument('--output',type=Path,required=True);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--source-sha',required=True)
    p=sub.add_parser('inspect');p.add_argument('--bundle',type=Path,required=True)
    p=sub.add_parser('apply');p.add_argument('--bundle',type=Path,required=True);p.add_argument('--root',type=Path,default=ROOT)
    p=sub.add_parser('publish');p.add_argument('--bundle',type=Path,required=True);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--run-id',default=os.environ.get('GITHUB_RUN_ID',''))
    p=sub.add_parser('verify-public');p.add_argument('--account',required=True);p.add_argument('--sha',required=True);p.add_argument('--require-fresh',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.command=='bundle':pack(args.root,args.output,args.source_sha)
        elif args.command=='inspect':
            manifest,_=inspect(args.bundle);print(json.dumps(manifest,indent=2))
        elif args.command=='apply':apply(args.bundle,args.root);print('Candidate applied; run the complete test suite before publication.')
        elif args.command=='publish':publish(args.root,args.bundle,run_id=args.run_id)
        else:check_public(args.account,args.sha,require_fresh=args.require_fresh)
    except (ReleaseError,OSError,subprocess.CalledProcessError) as exc:
        print(f'PROFILE_RELEASE_ERROR: {exc}',file=sys.stderr)
        return 1
    return 0

if __name__=='__main__':
    raise SystemExit(main())
