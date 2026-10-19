#!/usr/bin/env bash
# Publish the approved public copy: GitHub main (open source) and beta (Render deploys it after CI).
# Run only after the owner approves a release.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
git -c credential.helper= -c "credential.helper=!$ROOT/.tools/bin/gh auth git-credential" push origin public:main public:beta
