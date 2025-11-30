#!/usr/bin/env bash
set -euo pipefail

ORG_ALIAS="${SFDX_ORG_ALIAS:-Sandbox}"

echo "Validating source deploy to org: ${ORG_ALIAS}"

sfdx force:source:deploy \
  -p force-app \
  -u "${ORG_ALIAS}" \
  -c \
  -l RunLocalTests
