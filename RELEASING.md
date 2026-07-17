# Releasing WingTip

This checklist prepares and publishes a WingTip release without making the package build depend on repository-local state.

## Prerequisites

- Confirm the intended version in `pyproject.toml`, `config.json`, and `docs/changelog.md`
- Confirm the version does not already exist on PyPI or as a Git tag
- Require a clean working tree and a green `main` branch
- Configure a PyPI account with two-factor authentication or a trusted publisher
- Never commit a PyPI token to the repository, shell history, workflow logs, or configuration files

## Build and inspect

Create distributions from a clean checkout:

```bash
python -m build
python -m twine check dist/*
```

Inspect the archive contents:

```bash
python -m zipfile --list dist/wingtip-0.4.1-py3-none-any.whl
```

The wheel must include `wingtip/template.html`, `wingtip/static/`, and `wingtip/fonts/`.

## Cold-install test

Test the built wheel outside the source checkout:

```bash
python -m venv /tmp/wingtip-release
/tmp/wingtip-release/bin/pip install dist/wingtip-0.4.1-py3-none-any.whl
mkdir -p /tmp/wingtip-release-project/docs
printf '# Release fixture\n' > /tmp/wingtip-release-project/README.md
printf '# Install\n' > /tmp/wingtip-release-project/docs/install.md
/tmp/wingtip-release/bin/wingtip --source /tmp/wingtip-release-project --output /tmp/wingtip-release-site
/tmp/wingtip-release/bin/wingtip --version
python audit_site.py --output /tmp/wingtip-release-site --project-name 'Release fixture'
```

Confirm `wingtip --help` contains only installed-command usage and current positioning.

## Optional TestPyPI check

```bash
python -m twine upload --repository testpypi dist/*
```

Install from TestPyPI in a fresh environment before using production PyPI. Dependency resolution may require the normal PyPI index.

## Tag and GitHub release

Only after the exact commit has passed CI:

```bash
git tag -s v0.4.1 -m 'WingTip v0.4.1'
git push origin v0.4.1
```

Create the GitHub release from `v0.4.1` and use the matching section from `docs/changelog.md` as release notes. Attach the wheel and source archive produced from the tagged commit.

## Publish to PyPI

```bash
python -m twine upload dist/*
```

Prefer trusted publishing over a long-lived token when release automation is added.

## Verify after publishing

In a clean environment:

```bash
python -m venv /tmp/wingtip-pypi
/tmp/wingtip-pypi/bin/pip install wingtip==0.4.1
/tmp/wingtip-pypi/bin/wingtip --version
/tmp/wingtip-pypi/bin/wingtip --help
```

Verify the PyPI project metadata, README rendering, source links, license, supported Python versions, and package files. Then update installation documentation only if the published command differs from the tested workflow.

## Branch cleanup

After the release is verified:

- Delete remote branches already merged into `main`
- Inspect unmerged branches before deletion; do not infer safety from branch names
- Close or merge superseded pull requests
- Keep protected branches and any branch tied to an active release or migration
- Run `git fetch --prune` locally after remote cleanup
