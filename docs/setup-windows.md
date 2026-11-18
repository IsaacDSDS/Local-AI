# Setup on Windows

Target machine: RX 6700 XT (12 GB), 32 GB RAM, Windows 11.

## 1. GPU driver

Install the current AMD Adrenalin driver; it includes the Vulkan driver colibri
uses. In the BIOS, turn on **Resizable BAR / Smart Access Memory**: colibri works
without it, but it is the recommended setup for loading weights into VRAM.

## 2. colibri + Qwen3.6-35B-A3B

Put the models on an NVMe drive with at least 30 GB free.

```bat
git clone https://github.com/JustVugg/colibri
cd colibri
START-HERE.bat --model qwen36-35b --backend vulkan
```

`START-HERE.bat` installs Python with winget if it's missing, gets the engine
(the prebuilt release runs on Vulkan with nothing to build), downloads the model
(23 GB, resumable: run it again if it stops) and starts the server on
`http://127.0.0.1:8000`. `--dir D:\models` puts the models on another drive.

Next times: run `START-HERE.bat` again, or `c\coli.cmd status` / `c\coli.cmd stop`.

Check the GPU is in use: the setup output should say it chose Vulkan. Free VRAM
helps (each GB holds more experts): close games and GPU-heavy browser tabs.

## 3. Python tools: pipx and lai

Python 3.10+ is already there after step 2.

```powershell
py -m pip install --user pipx
py -m pipx ensurepath          # then open a new terminal
git clone https://github.com/IsaacDSDS/Local-AI.git
cd Local-AI
pipx install -e .
lai status
```

## 4. Claude Code

Install Claude Code for Windows (it needs Git for Windows, which provides Git
Bash; `lai task` runs its checks there too). Then, in each project where you want
delegation, append [`templates/CLAUDE.md`](../templates/CLAUDE.md) to the
project's `CLAUDE.md`.

Then go through [verify-first-run.md](verify-first-run.md).
