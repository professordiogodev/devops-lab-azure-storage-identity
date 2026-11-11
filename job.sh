#!/bin/bash
# PROVIDED. This is what a container job runs. It signs in with the managed identity it was given (no password, no key),
# tries to read the container, then tries to write a receipt, and prints what happened.
# Environment: CLIENT_ID (the identity), ACCOUNT (storage account), RUN (a label)
az login --identity --client-id "$CLIENT_ID" --allow-no-subscriptions >/dev/null 2>&1 || { echo "LOGIN_FAILED"; exit 0; }
echo "{\"order\": \"$RUN\", \"total_cents\": 700}" > /tmp/receipt.json
if az storage blob list --account-name "$ACCOUNT" -c receipts --auth-mode login -o tsv >/tmp/list.txt 2>/tmp/list.err; then echo "READ_OK"; else echo "READ_DENIED: $(grep -oE 'AuthorizationPermissionMismatch|AuthorizationFailure|AuthenticationFailed|ErrorCode:[A-Za-z]+' /tmp/list.err | head -1)"; fi
if az storage blob upload --account-name "$ACCOUNT" -c receipts -n "receipt-$RUN.json" -f /tmp/receipt.json --auth-mode login --overwrite >/dev/null 2>/tmp/up.err; then echo "WRITE_OK"; else echo "WRITE_DENIED: $(grep -oE 'AuthorizationPermissionMismatch|AuthorizationFailure|AuthenticationFailed|ErrorCode:[A-Za-z]+' /tmp/up.err | head -1)"; fi
