#!/usr/bin/env bash
set -euo pipefail

ORG_ALIAS="${SFDX_ORG_ALIAS:-Sandbox}"
THRESHOLD="${COVERAGE_THRESHOLD:-75}"

RESULT_DIR="tests/apex"
RESULT_FILE="${RESULT_DIR}/apex-result.json"

mkdir -p "${RESULT_DIR}"

echo "Running Apex tests in org: ${ORG_ALIAS}"
echo "Coverage threshold: ${THRESHOLD}%"

sfdx force:apex:test:run \
  -u "${ORG_ALIAS}" \
  --resultformat json \
  --codecoverage \
  --wait 60 \
  --outputdir "${RESULT_DIR}" \
  -c

# sfdx generates files with timestamps, get the latest one
LATEST_FILE=$(ls -t "${RESULT_DIR}" | grep "test-result" | head -n 1)
mv "${RESULT_DIR}/${LATEST_FILE}" "${RESULT_FILE}"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required but not installed."
  exit 1
fi

# Covarage is given as an average of all classes
COVERAGE_INT=$(jq '[.codecoverage[].percentage] | add / length | floor' "${RESULT_FILE}")

echo "Average coverage: ${COVERAGE_INT}%"

if [ "${COVERAGE_INT}" -lt "${THRESHOLD}" ]; then
  echo "Code coverage ${COVERAGE_INT}% is below threshold ${THRESHOLD}%"
  exit 1
fi

echo "Apex tests passed and coverage threshold met."
