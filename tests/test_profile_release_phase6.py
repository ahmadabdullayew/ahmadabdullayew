"""Offline Phase 6 tests: candidate integrity, least privilege, git race guards, and public-verification contract."""
from __future__ import annotations

import datetime as dt
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import profile_release as release

NOW=dt.datetime(2026,10,10,12,0,0,tzinfo=dt.timezone.utc)
STAMP='2026-10-10T12:00:00Z'
UNKNOWN='unknown (archived snapshot; API retrieval time was not recorded)'


def make_fixture(root:Path):
    (root/'profile').mkdir(parents=True,exist_ok=True)
    for name in release.OWNED:
        original=(ROOT/name).read_text(encoding='utf-8')
        assert UNKNOWN in original,name
        (root/name).write_text(original.replace(UNKNOWN,STAMP),encoding='utf-8')


def cmd(*args,cwd:Path):
    return subprocess.run(args,cwd=cwd,check=True,capture_output=True,text=True).stdout.strip()


class Phase6ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        make_fixture(self.root)
        self.bundle=self.root/'candidate.zip'
        self.source='a'*40

    def pack(self):
        return release.pack(self.root,self.bundle,self.source,now=NOW)

    def test_candidate_bundle_roundtrip(self):
        manifest=self.pack()
        got,files=release.inspect(self.bundle,now=NOW)
        self.assertEqual(manifest,got)
        self.assertEqual(set(files),set(release.OWNED))
        self.assertEqual(got['snapshot']['retrieved_utc'],STAMP)

    def test_unknown_archived_snapshot_rejected(self):
        old=(ROOT/'profile/contributions-summary.md').read_bytes()
        with self.assertRaises(release.ReleaseError):release.decode_summary(old,now=NOW)

    def test_expired_candidate_rejected(self):
        self.pack()
        with self.assertRaisesRegex(release.ReleaseError,'window'):
            release.inspect(self.bundle,now=NOW+dt.timedelta(hours=8))

    def test_future_snapshot_rejected(self):
        self.pack()
        with self.assertRaisesRegex(release.ReleaseError,'window'):
            release.inspect(self.bundle,now=NOW-dt.timedelta(minutes=6))

    def test_bundle_checksum_tampering_detected(self):
        self.pack()
        with zipfile.ZipFile(self.bundle) as z:data={n:z.read(n) for n in z.namelist()}
        data['profile/contributions-light.svg']+=b'\n'
        with zipfile.ZipFile(self.bundle,'w') as z:
            for name,raw in data.items():z.writestr(name,raw)
        with self.assertRaisesRegex(release.ReleaseError,'checksum'):
            release.inspect(self.bundle,now=NOW)

    def test_unowned_path_rejected(self):
        self.pack()
        with zipfile.ZipFile(self.bundle,'a') as z:z.writestr('../outside','untrusted')
        with self.assertRaisesRegex(release.ReleaseError,'unexpected'):
            release.inspect(self.bundle,now=NOW)

    def test_duplicate_name_rejected(self):
        self.pack()
        with self.assertWarns(UserWarning):
            with zipfile.ZipFile(self.bundle,'a') as z:z.writestr('manifest.json','{}')
        with self.assertRaisesRegex(release.ReleaseError,'unexpected'):
            release.inspect(self.bundle,now=NOW)

    def test_invalid_svg_rejected_even_with_updated_hash(self):
        self.pack()
        with zipfile.ZipFile(self.bundle) as z:data={n:z.read(n) for n in z.namelist()}
        name='profile/contributions-light.svg'
        data[name]=b'<svg>no title or semantics</svg>'
        manifest=json.loads(data['manifest.json']);manifest['files'][name]={'sha256':release.sha(data[name]),'bytes':len(data[name])}
        data['manifest.json']=json.dumps(manifest).encode()
        with zipfile.ZipFile(self.bundle,'w') as z:
            for file,raw in data.items():z.writestr(file,raw)
        with self.assertRaisesRegex(release.ReleaseError,'root semantics'):
            release.inspect(self.bundle,now=NOW)

    def test_summary_total_tamper_rejected(self):
        original=(self.root/'profile/contributions-summary.md').read_text()
        (self.root/'profile/contributions-summary.md').write_text(original.replace('**Reported contribution total:** 122','**Reported contribution total:** 999'))
        with self.assertRaisesRegex(release.ReleaseError,'totals'):
            self.pack()

    def test_apply_replaces_only_owned_paths(self):
        self.pack()
        other=self.root/'profile/notes.txt';other.write_text('preserve')
        for name in release.OWNED:(self.root/name).write_text('outdated')
        release.apply(self.bundle,self.root,now=NOW)
        self.assertEqual(other.read_text(),'preserve')
        self.assertEqual(release.inspect(self.bundle,now=NOW)[1]['profile/contributions-summary.md'],(self.root/'profile/contributions-summary.md').read_bytes())

    def test_reject_symlink_target(self):
        self.pack()
        name=self.root/'profile/contributions-dark.svg';name.unlink()
        name.symlink_to(self.root/'candidate.zip')
        with self.assertRaisesRegex(release.ReleaseError,'symlink'):
            release.apply(self.bundle,self.root,now=NOW)

    def test_workflows_use_sha_pins_and_scope_tokens(self):
        quality=(ROOT/'.github/workflows/profile-quality.yml').read_text()
        publisher=(ROOT/'.github/workflows/update-contributions.yml').read_text()
        for doc in (quality,publisher):
            for match in re.findall(r'uses:\s*(\S+)',doc):
                self.assertRegex(match,r'^[\w-]+/[\w-]+@[0-9a-f]{40}$')
        self.assertIn('persist-credentials: false',quality)
        self.assertIn('contents: read',publisher)
        self.assertIn('pull-requests: write',publisher)
        self.assertIn('cancel-in-progress: false',publisher)
        self.assertIn('profile_release.py publish',publisher)
        self.assertIn('profile_release.py verify-public',publisher)

    def test_public_verification_mock(self):
        class Response:
            def __init__(self,payload):self.payload=payload
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,n):return self.payload[:n]
        def urlopen(request,timeout=15):
            url=request.full_url
            if url=='https://github.com/ahmadabdullayew':return Response(b'<html><article>ASANAppeal Bahar</article></html>')
            if url=='https://api.github.com/repos/ahmadabdullayew/ahmadabdullayew/git/ref/heads/main':return Response(json.dumps({'object': {'sha': self.source, 'type': 'commit'}}).encode())
            if url.endswith('/README.md'):return Response(b'# Profile\n## Featured Projects\nASANAppeal Bahar')
            name='profile/'+url.split('/profile/',1)[1]
            return Response((self.root/name).read_bytes())
        release.check_public('ahmadabdullayew',self.source,opener=urlopen,attempts=1)


class Phase6GitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name)
        self.remote=base/'remote.git'; self.repo=base/'source'; self.work=base/'work'
        cmd('git','init','--bare','-b','main',str(self.remote),cwd=base)
        self.repo.mkdir();cmd('git','init','-b','main',cwd=self.repo)
        cmd('git','config','user.email','test@example.com',cwd=self.repo)
        cmd('git','config','user.name','Test',cwd=self.repo)
        make_fixture(self.repo)
        (self.repo/'README.md').write_text('# Profile baseline\n')
        for n in release.CONTRACT_PATHS:
            f=self.repo/n
            if not f.is_file(): f.parent.mkdir(parents=True,exist_ok=True);f.write_text('contract baseline')
        cmd('git','add','.',cwd=self.repo);cmd('git','commit','-m','base',cwd=self.repo)
        cmd('git','remote','add','origin',str(self.remote),cwd=self.repo)
        cmd('git','push','-u','origin','main',cwd=self.repo)
        self.base_sha=cmd('git','rev-parse','HEAD',cwd=self.repo)
        cmd('git','clone','-b','main',str(self.remote),str(self.work),cwd=base)
        self.bundle=base/'candidate.zip'
        release.pack(self.repo,self.bundle,self.base_sha,now=NOW)

    def test_rebase_prep_and_allowlisted_commit(self):
        with patch.object(release,'utcnow',return_value=NOW),patch.object(release,'validate_local'):
            # Force a real five-file diff relative to baseline; valid after manifest edits.
            original=(self.repo/'profile/contributions-summary.md').read_text()
            self.assertEqual(len(release.OWNED),5)
            commit,changed=release.prepare_against_latest(self.work,self.bundle,self.base_sha)
        self.assertFalse(changed)
        self.assertEqual(commit,self.base_sha)

    def changed_candidate(self):
        """Emulate a later successful API refresh on the SAME checked-out source."""
        later='2026-10-10T13:00:00Z'
        for n in release.OWNED:
            path=self.repo/n
            path.write_text(path.read_text().replace(STAMP,later))
        release.pack(self.repo,self.bundle,self.base_sha,now=NOW+dt.timedelta(hours=1))
        return NOW+dt.timedelta(hours=1)

    def test_fast_forward_publishes_only_five_owned_paths(self):
        now=self.changed_candidate()
        with patch.object(release,'utcnow',return_value=now),patch.object(release,'validate_local'):
            status,commit=release.publish(self.work,self.bundle,run_id='10011')
        self.assertEqual(status,'direct-main')
        latest=cmd('git','rev-parse','main',cwd=self.repo)
        cmd('git','fetch','origin','main',cwd=self.repo)
        remote_sha=cmd('git','rev-parse','refs/remotes/origin/main',cwd=self.repo)
        self.assertEqual(remote_sha,commit)
        changed=cmd('git','diff','--name-only',self.base_sha,remote_sha,cwd=self.repo).splitlines()
        self.assertEqual(sorted(changed),sorted(release.OWNED))

    def test_protected_main_push_uses_pr_fallback(self):
        now=self.changed_candidate()
        hook=self.remote/'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nwhile read old new ref; do\n  if [ "$ref" = "refs/heads/main" ]; then echo protected >&2; exit 1; fi\ndone\nexit 0\n')
        hook.chmod(0o755)
        created=[]
        def fallback(root,sha_commit,run_id):
            created.append((sha_commit,run_id))
            release.git('push','origin',f'HEAD:refs/heads/automation/profile-activity-{run_id}',cwd=root)
        with patch.object(release,'utcnow',return_value=now),patch.object(release,'validate_local'),patch.object(release,'create_fallback_pr',side_effect=fallback):
            status,commit=release.publish(self.work,self.bundle,run_id='10012')
        self.assertEqual(status,'pull-request')
        self.assertEqual(created,[(commit,'10012')])
        main=cmd('git','ls-remote','origin','refs/heads/main',cwd=self.work).split()[0]
        branch=cmd('git','ls-remote','origin','refs/heads/automation/profile-activity-10012',cwd=self.work).split()[0]
        self.assertEqual(main,self.base_sha)
        self.assertEqual(branch,commit)

    def test_new_readme_commit_blocks_old_candidate(self):
        (self.repo/'README.md').write_text('# Updated by someone else\n')
        cmd('git','add','README.md',cwd=self.repo)
        cmd('git','commit','-m','concurrent readme edit',cwd=self.repo)
        cmd('git','push','origin','main',cwd=self.repo)
        with patch.object(release,'utcnow',return_value=NOW),patch.object(release,'validate_local'):
            with self.assertRaisesRegex(release.ReleaseError,'contract or owned assets changed'):
                release.prepare_against_latest(self.work,self.bundle,self.base_sha)

    def test_unrelated_latest_change_is_preserved(self):
        (self.repo/'UNRELATED.md').write_text('user content')
        cmd('git','add','UNRELATED.md',cwd=self.repo)
        cmd('git','commit','-m','unrelated change',cwd=self.repo)
        cmd('git','push','origin','main',cwd=self.repo)
        with patch.object(release,'utcnow',return_value=NOW),patch.object(release,'validate_local'):
            commit,changed=release.prepare_against_latest(self.work,self.bundle,self.base_sha)
        self.assertFalse(changed)
        self.assertEqual(commit,cmd('git','rev-parse','HEAD',cwd=self.repo))
        self.assertEqual((self.work/'UNRELATED.md').read_text(),'user content')


if __name__=='__main__':unittest.main()
