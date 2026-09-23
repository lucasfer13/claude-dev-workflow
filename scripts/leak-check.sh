#!/usr/bin/env bash
# Fails when tracked files mention private names. Run before every push.
# Extra terms (company, hosts, people) go in .leak-terms — one regex per line, never committed.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
pattern='@[a-z0-9-]+\.(es|com|org)\b|[A-Za-z]:\\\\|/c/Users/|glpat-|ghp_[A-Za-z0-9]{20}|BEGIN (RSA|OPENSSH) PRIVATE KEY'
if [[ -f .leak-terms ]]; then
  extra=$(grep -v '^\s*$' .leak-terms | paste -sd'|' -)
  [[ -n "$extra" ]] && pattern="$pattern|$extra"
fi
hits=$(git ls-files -z | xargs -0 grep -nIiE "$pattern" -- 2>/dev/null | grep -v '^scripts/leak-check.sh:' | grep -viE '@(github|gitlab).com[:/]|noreply@anthropic|users\.noreply\.github\.com|example\.(com|org)' || true)
if [[ -n "$hits" ]]; then
  echo "$hits"
  echo "leak-check: FAILED"
  exit 1
fi
echo "leak-check: clean"
