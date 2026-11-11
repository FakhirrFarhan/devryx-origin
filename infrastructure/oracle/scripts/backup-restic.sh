#!/usr/bin/env bash
set -euo pipefail

: "${RESTIC_REPOSITORY:?Set RESTIC_REPOSITORY in a protected environment file}"
: "${RESTIC_PASSWORD_FILE:?Set RESTIC_PASSWORD_FILE to a protected password file}"

if [[ ! -r "$RESTIC_PASSWORD_FILE" ]]; then
  echo "Restic password file is missing or unreadable." >&2
  exit 1
fi

# Adjust paths to actual persistent data locations. Do not back up secrets
# from the repository blindly; decide what must be backed up and encrypt it.
PATHS=()
[[ -d /opt/devryx/data ]] && PATHS+=(/opt/devryx/data)
[[ -d /opt/devryx/config-backup ]] && PATHS+=(/opt/devryx/config-backup)

if [[ ${#PATHS[@]} -eq 0 ]]; then
  echo "No configured backup paths found. Configure /opt/devryx/data first." >&2
  exit 1
fi

restic backup "${PATHS[@]}" --tag devryx
restic forget --keep-hourly 24 --keep-daily 14 --keep-weekly 8 --keep-monthly 6 --prune
