#!/usr/bin/env bash
set -euo pipefail
# Run only after confirming SSH key access in a second terminal.
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw --force enable
sudo ufw status verbose
