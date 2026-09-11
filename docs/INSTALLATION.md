# Installing TongaLang

TongaLang 0.2.0 is available as a per-user Windows installer. Linux users can
install from source or build a native standalone bundle. The Windows and Linux
builds use the same lexer, parser, interpreter and Tkinter IDE.

## Windows installer

1. Open the [latest TongaLang release](https://github.com/leomabuku/PROJECT/releases/latest).
2. Download `TongaLang-Setup-0.2.0.exe` and its `.sha256` file.
3. Double-click the setup file and select **Install TongaLang**.
4. Open TongaLang from the Start Menu or the optional Desktop shortcut.

The installer does not need administrator access. It installs into:

```text
%LOCALAPPDATA%\Programs\TongaLang
```

All 17 example programs are installed directly in
`%LOCALAPPDATA%\Programs\TongaLang\Examples`, with the language reference and
installation guide in the neighbouring `Documentation` folder.
To remove the application, use **Settings → Apps → Installed apps → TongaLang**
or the **Uninstall TongaLang** Start Menu shortcut.

### Windows security notice

The current release is not digitally code-signed. Windows SmartScreen may show
an “unrecognized app” message even when the checksum is correct. Download only
from the official GitHub repository, compare the SHA-256 checksum, then choose
**More info → Run anyway** if you trust the download.

Check a download in PowerShell:

```powershell
Get-FileHash .\TongaLang-Setup-0.2.0.exe -Algorithm SHA256
Get-Content .\TongaLang-Setup-0.2.0.exe.sha256
```

## Building the Windows installer

Requirements:

- Windows 10 or newer
- Python 3.10 or newer, including Tkinter
- PowerShell 5.1 or newer
- .NET Framework 4.x (included with supported Windows versions)
- Git

Build from a clean clone:

```powershell
git clone https://github.com/leomabuku/PROJECT.git TongaLang
cd TongaLang
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\distribution\windows\build_installer.ps1
```

The command packages the IDE with PyInstaller, compiles the small setup and
uninstaller programs with the Windows .NET Framework compiler, then writes:

```text
dist\TongaLang-Setup-0.2.0.exe
dist\TongaLang-Setup-0.2.0.exe.sha256
```

PyInstaller must run on Windows to produce a Windows executable. Building it on
Linux does not create a Windows `.exe` unless a separately maintained Windows
build environment is used.

## Installing on Linux from source

Install Python, virtual-environment support and Tkinter first.

Ubuntu or Debian:

```bash
sudo apt update
sudo apt install git python3 python3-venv python3-tk
```

Fedora:

```bash
sudo dnf install git python3 python3-tkinter
```

Arch Linux:

```bash
sudo pacman -S git python tk
```

Then install TongaLang for the current user:

```bash
git clone https://github.com/leomabuku/PROJECT.git TongaLang
cd TongaLang
chmod +x distribution/linux/install.sh
./distribution/linux/install.sh
```

Open the IDE from the application menu or run:

```bash
~/.local/bin/tongalang-ide
```

Run a source file from a terminal with:

```bash
~/.local/bin/tongalang examples/01_mazyina.tg
```

If `~/.local/bin` is not already on `PATH`, add this line to `~/.bashrc` or the
configuration file used by your shell:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Building a standalone Linux bundle

Linux bundles must be built on a compatible Linux system. After installing the
distribution packages shown above:

```bash
git clone https://github.com/leomabuku/PROJECT.git TongaLang
cd TongaLang
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt
chmod +x distribution/linux/build.sh
./distribution/linux/build.sh
```

The archive is written to:

```text
dist/TongaLang-linux-x86_64-0.2.0.tar.gz
```

Extract it and run `TongaLang/TongaLang`. A bundle built on one Linux
distribution may not run on a substantially older distribution because system
libraries such as glibc are supplied by the host.

## Troubleshooting

- If the Linux IDE reports that Tkinter is missing, install the Tk package for
  the exact Python version supplied by your distribution.
- A Linux desktop session with a graphical display is required for the IDE.
  The command-line runner can still be used in a terminal-only environment.
- If antivirus software quarantines an unsigned Windows build, verify the
  checksum and submit the file to the antivirus vendor for review rather than
  disabling protection.
- Report reproducible packaging problems through the repository’s GitHub issue
  tracker, including the operating-system version and exact error message.
