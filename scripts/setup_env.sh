#!/bin/bash
# setup_env.sh - Install dependencies and setup Python environment

# Detect architecture
ARCH=$(uname -m)
echo "Setting up environment for architecture: $ARCH"

# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
    libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
    gcc make build-essential

# Install pyenv
if [ ! -d "$HOME/.pyenv" ]; then
    echo "Installing pyenv..."
    curl https://pyenv.run | bash
fi

# Configure pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc 