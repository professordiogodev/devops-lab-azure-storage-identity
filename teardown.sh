#!/usr/bin/env bash
# Deletes the resource group and everything in it. Run with: ./teardown.sh
set -u
cd "$(dirname "$0")"
az account show >/dev/null 2>&1 || { echo "Not logged in to Azure (az login)." >&2; exit 1; }
if az group exists -n rg-beanie-receipts | grep -q true; then
  echo "Deleting resource group rg-beanie-receipts..."
  az group delete -n rg-beanie-receipts --yes
fi
echo "Now run ./verify-teardown.sh"
