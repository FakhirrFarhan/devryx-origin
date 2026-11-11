#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -eq 0 ]]; then
  echo "Run as the ubuntu user, not root." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl git unzip ufw fail2ban jq restic

# Install Docker using Docker's convenience script. Review this method for
# production policy before use; pin package versions for a hardened build.
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
sudo sh /tmp/get-docker.sh
rm -f /tmp/get-docker.sh
sudo usermod -aG docker "$USER"

sudo systemctl enable --now docker
sudo systemctl enable --now fail2ban

echo "Docker installed. Log out and reconnect for docker group membership."
echo "Next: verify SSH works, then run scripts/firewall-initial.sh."
