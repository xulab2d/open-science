#!/bin/zsh
set -eu

echo "Mounted volumes:"
ls /Volumes
echo
echo "Active Xu Lab mounts:"
mount | rg "Xu Lab|smbfs" || true
