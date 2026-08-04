# Install Profile V3

Target repository:

```text
https://github.com/ahmadabdullayew/ahmadabdullayew
```

## Safe update from Ubuntu

```bash
cd ~/Projects

rm -rf ahmadabdullayew-profile-repo

git clone \
  https://github.com/ahmadabdullayew/ahmadabdullayew.git \
  ahmadabdullayew-profile-repo

cd ahmadabdullayew-profile-repo
```

Copy the V3 package contents into the clone:

```bash
cp -a \
  ~/Projects/ahmadabdullayew-profile-v3/. \
  ~/Projects/ahmadabdullayew-profile-repo/
```

Review:

```bash
cd ~/Projects/ahmadabdullayew-profile-repo

git status
git diff -- README.md
find assets profile .github/workflows -maxdepth 2 -type f | sort
```

Publish:

```bash
git add \
  README.md \
  INSTALL.md \
  SETUP_WIDGETS.md \
  assets/ \
  profile/ \
  optional/ \
  .github/workflows/

git commit -m \
  "feat(profile): add curated visual analytics system"

git push origin main
```

Then follow `SETUP_WIDGETS.md`.
