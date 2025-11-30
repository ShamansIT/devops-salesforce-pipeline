#!/usr/bin/env bash
set -euo pipefail

echo "Installing Salesforce Code Analyzer (sfdx-scanner)..."
sfdx plugins:install @salesforce/sfdx-scanner@latest

echo "Running static analysis on force-app..."
sfdx scanner:run \
  --target "force-app" \
  --format "sarif" \
  --outfile "sf-code-scanner-results.sarif" \
  --severity-threshold 2
