# Setup on CachyOS (or any Arch-based distro)

## 1. Packages

```bash
sudo pacman -S --needed git python python-pipx base-devel vulkan-radeon vulkan-tools
vulkaninfo --summary        # the RX 6700 XT must be listed (RADV driver)
```

`vulkan-radeon` is Mesa's AMD Vulkan driver (RADV); CachyOS usually ships it.
If colibri's build asks for another package (Vulkan headers, the shader
compiler), it prints the exact command: run it, then the setup again.

Turn on **Resizable BAR / Smart Access Memory** in the BIOS.

## 2. colibri + Qwen3.6-35B-A3B

Keep the models on the Linux NVMe (default `~/colibri-models`).

```bash
git clone https://github.com/JustVugg/colibri
cd colibri
./start-here.sh --model qwen36-35b --backend vulkan
```

Next times: `./start-here.sh` starts it; `c/coli status`, `c/coli stop`,
`c/coli logs -n 50`. After a `git pull`, run `./start-here.sh` again to rebuild.

## 3. lai

```bash
git clone https://github.com/IsaacDSDS/Local-AI.git
cd Local-AI
pipx install -e .
lai status
```

## 4. Claude Code

Install Claude Code, then append [`templates/CLAUDE.md`](../templates/CLAUDE.md)
to the `CLAUDE.md` of each project where you want delegation.

Then go through [verify-first-run.md](verify-first-run.md).
