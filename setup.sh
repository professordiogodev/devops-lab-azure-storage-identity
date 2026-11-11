#!/usr/bin/env bash
# Checks your tools and your Azure login. Creates nothing in Azure. Run: ./setup.sh
set -u
cd "$(dirname "$0")"
for c in az curl python3; do command -v "$c" >/dev/null || { echo "MISSING: $c"; exit 1; }; done
az account show >/dev/null 2>&1 || { echo "Not logged in to Azure. Run: az login"; exit 1; }
cat <<TXT
Ready.
  Subscription:    $(az account show --query name -o tsv)
  You are:         $(az account show --query user.name -o tsv)
  Resource group:  rg-beanie-receipts   (region: eastus)
  Names to use:    storage account st<something unique, 3-24 lowercase letters/digits>, container receipts,
                   managed identities id-writer and id-reader
  Provided:        job.sh   (what the two container jobs run; read it)
Nothing exists in Azure yet.
TXT
