#!/usr/bin/env bash
rc=0
grep -rEq '(AccountKey|SharedAccessSignature|sig=)[A-Za-z0-9+/=%]{20,}' . --exclude-dir=.git --exclude=azcheck.py && { echo "- ❌ a storage key or SAS token is committed"; rc=1; } || echo "- ✅ no storage key or SAS token committed"
grep -qE '^ALL CHECKS PASSED \(' SUBMISSION.md && echo "- ✅ SUBMISSION.md shows ALL CHECKS PASSED" || { echo "- ❌ paste the verify.sh output ('ALL CHECKS PASSED') into SUBMISSION.md"; rc=1; }
exit $rc
