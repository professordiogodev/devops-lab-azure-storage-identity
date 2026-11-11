#!/usr/bin/env bash
# Proves the lab left nothing in Azure. Run with: ./verify-teardown.sh
set -u
cd "$(dirname "$0")"
SUB=$(az account show --query name -o tsv 2>/dev/null) || { echo "Not logged in to Azure (az login)." >&2; exit 1; }
echo "Checking subscription $SUB"
pass=0; failn=0
check() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then echo "PASS  $d"; pass=$((pass+1)); else echo "FAIL  $d"; failn=$((failn+1)); fi; }
check "the resource group rg-beanie-receipts no longer exists" bash -c 'az group exists -n rg-beanie-receipts | grep -q false'
check "no resource tagged lab=azure-storage-identity anywhere in the subscription" bash -c '[ -z "$(az resource list --tag lab=azure-storage-identity --query "[].id" -o tsv)" ]'
echo
if [ "$failn" -eq 0 ]; then echo "TEARDOWN VERIFIED ($pass/$pass) in subscription $SUB"; else echo "NOT CLEAN: $failn leftover(s). Remove them and run this again."; fi
exit "$failn"
