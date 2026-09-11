#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

python3 -m PyInstaller --noconfirm --clean --onedir --windowed \
  --name TongaLang --icon "$repo_root/assets/branding/tongalang-logo.png" \
  --paths "$repo_root" --collect-submodules ply \
  --add-data "assets:assets" \
  --add-data "README.md:." \
  --add-data "TONGALANG_LANGUAGE_REFERENCE.md:." \
  --add-data "examples:examples" \
  distribution/app_entry.py

tar -C dist -czf "dist/TongaLang-linux-x86_64-0.2.0.tar.gz" TongaLang
echo "Built dist/TongaLang-linux-x86_64-0.2.0.tar.gz"
