#!/usr/bin/env bash
# Shared scanning logic for the pre-commit and commit-msg hooks.
# Sourced, not run. Pure bash plus grep.
#
# The denylist is read only through the PORTFOLIO_DENYLIST environment
# variable. Its terms are never printed. On a hit, only the category and
# the file name are reported.

# Fail closed: the scan must not pass when it cannot run.
check_denylist_env() {
  if [ -z "${PORTFOLIO_DENYLIST:-}" ]; then
    echo "hook: PORTFOLIO_DENYLIST is not set. Refusing to commit (fail closed)." >&2
    return 1
  fi
  if [ ! -f "$PORTFOLIO_DENYLIST" ] || [ ! -r "$PORTFOLIO_DENYLIST" ]; then
    echo "hook: the denylist file is missing or unreadable. Refusing to commit (fail closed)." >&2
    return 1
  fi
  if [ ! -s "$PORTFOLIO_DENYLIST" ]; then
    echo "hook: the denylist file is empty. Refusing to commit (fail closed)." >&2
    return 1
  fi
  if grep -q '^[[:space:]]*$' "$PORTFOLIO_DENYLIST"; then
    echo "hook: the denylist file has a blank line, which would match everything. Refusing to commit (fail closed)." >&2
    return 1
  fi
  return 0
}

# Generic patterns, one per category. Written so that the patterns do not
# match their own source text.
GENERIC_CATEGORIES=(
  "private-key-header"
  "github-token"
  "api-secret-key"
  "aws-access-key-id"
  "private-ipv4-address"
  "absolute-home-path"
)
GENERIC_PATTERNS=(
  'BEGIN [A-Z ]*PRIVATE KEY'
  '(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})'
  'sk-[A-Za-z0-9_-]{20,}'
  'AKIA[0-9A-Z]{16}'
  '(^|[^0-9.])(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.[0-9]{1,3}\.[0-9]{1,3})([^0-9.]|$)'
  '/(home|Users)/[a-z]'
)

# scan_text LABEL: reads text on stdin, prints one line per category hit,
# and returns 1 if anything matched.
scan_text() {
  local label="$1" text found=0 i
  text="$(cat)"
  [ -z "$text" ] && return 0
  if printf '%s\n' "$text" | grep -q -F -i -f "$PORTFOLIO_DENYLIST"; then
    echo "hook: BLOCKED [denylist-term] in $label" >&2
    found=1
  fi
  for i in "${!GENERIC_PATTERNS[@]}"; do
    if printf '%s\n' "$text" | grep -q -E -e "${GENERIC_PATTERNS[$i]}"; then
      echo "hook: BLOCKED [${GENERIC_CATEGORIES[$i]}] in $label" >&2
      found=1
    fi
  done
  return "$found"
}
