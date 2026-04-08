#!/usr/bin/env bash
set -euo pipefail

# Install MS core fonts (Times New Roman, Arial, etc.)
echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | sudo debconf-set-selections
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y ttf-mscorefonts-installer
rm -rf ~/.cache/matplotlib/fontlist* ~/.cache/matplotlib/*.json 2>/dev/null

# Install Python env + plotting dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH="$HOME/.local/bin:$PATH" && uv python install 3.12 && uv venv ~/xk-py --python 3.12 && ~/xk-py/bin/python -m ensurepip --upgrade && ~/xk-py/bin/python -m pip install --upgrade pip && uv pip install --python ~/xk-py/bin/python matplotlib numpy seaborn