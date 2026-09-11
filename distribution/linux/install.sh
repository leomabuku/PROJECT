#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
app_dir="$data_home/tongalang"
bin_dir="$HOME/.local/bin"
desktop_dir="$data_home/applications"

mkdir -p "$app_dir" "$bin_dir" "$desktop_dir"
python3 -m venv "$app_dir/venv"
"$app_dir/venv/bin/python" -m pip install --upgrade pip
"$app_dir/venv/bin/python" -m pip install -r "$repo_root/requirements.txt"

mkdir -p "$app_dir/source"
cp -R "$repo_root/tongalang" "$repo_root/gui" "$repo_root/examples" "$repo_root/assets" "$app_dir/source/"
cp "$repo_root/main.py" "$repo_root/README.md" "$repo_root/TONGALANG_LANGUAGE_REFERENCE.md" "$app_dir/source/"

cat > "$bin_dir/tongalang" <<EOF
#!/usr/bin/env bash
exec "$app_dir/venv/bin/python" "$app_dir/source/main.py" "\$@"
EOF
cat > "$bin_dir/tongalang-ide" <<EOF
#!/usr/bin/env bash
cd "$app_dir/source"
exec "$app_dir/venv/bin/python" -m gui.app "\$@"
EOF
chmod +x "$bin_dir/tongalang" "$bin_dir/tongalang-ide"

cat > "$desktop_dir/tongalang.desktop" <<EOF
[Desktop Entry]
Name=TongaLang
Comment=Beginner programming language using Tonga-derived keywords
Exec=$bin_dir/tongalang-ide
Icon=$app_dir/source/assets/branding/tongalang-logo.png
Terminal=false
Type=Application
Categories=Development;Education;
Keywords=programming;education;tonga;
EOF
chmod +x "$desktop_dir/tongalang.desktop"

echo "TongaLang is installed."
echo "IDE: $bin_dir/tongalang-ide"
echo "CLI: $bin_dir/tongalang path/to/program.tg"
echo "If commands are not found, add $bin_dir to PATH."
