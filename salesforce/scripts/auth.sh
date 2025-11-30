#!/usr/bin/env bash
set -euo pipefail

ORG_ALIAS="${SFDX_ORG_ALIAS:-Sandbox}"

if [ -z "${SFDX_AUTH_URL:-}" ]; then
  echo "SFDX_AUTH_URL is not set. Export it or configure GitHub secret."
  exit 1
fi

echo "Using org alias: ${ORG_ALIAS}"

# Save the auth URL to a temporary file
echo "${SFDX_AUTH_URL}" > sfdx_auth_url.txt

# Authenticate using the SFDX auth URL
sfdx auth:sfdxurl:store -f sfdx_auth_url.txt -s -a "${ORG_ALIAS}"

rm sfdx_auth_url.txt

echo "Authenticated org details:"
sfdx force:org:display -u "${ORG_ALIAS}"
