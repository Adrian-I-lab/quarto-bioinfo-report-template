#!/usr/bin/env bash
# Runs every unit test and every style check, then prints one table.
#
# Usage:
#   bash scripts/check_style.sh            check the whole book
#   bash scripts/check_style.sh --changed  content checks only on .qmd and .md
#                                          files changed against main
#   PYTHON=.venv/bin/python bash scripts/check_style.sh
#                                          use another Python (for example one
#                                          with numpy, so the setup tests run)
#
# Exits non-zero if any step failed, or if any step examined nothing.

set -euo pipefail

cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
TOOLS="tools/style"

changed=0
if [ "${1:-}" = "--changed" ]; then
  changed=1
fi

rows=()
status=0
logdir="$(mktemp -d)"
trap 'rm -rf "$logdir"' EXIT

# field NAME LINE: the value of NAME=value in a summary line, or 0.
field() {
  local v
  v="$(printf '%s\n' "$2" | grep -o "$1=[0-9]*" | head -1 | cut -d= -f2 || true)"
  echo "${v:-0}"
}

# record NAME EXAMINED ERRORS WARNINGS EXIT
record() {
  rows+=("$1|$2|$3|$4|$5")
  if [ "$5" != "0" ] && [ "$5" != "skipped" ]; then
    status=1
  fi
}

# run_check NAME CMD...: runs a check, parses its summary line.
run_check() {
  local name="$1" code=0 log summary examined errors warnings
  shift
  log="$logdir/$name.log"
  "$@" >"$log" 2>&1 || code=$?
  summary="$(tail -1 "$log")"
  examined="$(field files_examined "$summary")"
  errors="$(field errors "$summary")"
  if [ "$errors" = "0" ]; then
    errors="$(field violations "$summary")"
  fi
  warnings="$(field warnings "$summary")"
  if [ "$examined" = "0" ] && [ "$code" = "0" ]; then
    code=2
  fi
  if [ "$code" != "0" ]; then
    echo "---- $name (exit $code) ----"
    grep -v '^files_examined=' "$log" | head -40 || true
  fi
  record "$name" "$examined" "$errors" "$warnings" "$code"
}

# 1. Python unit tests.
code=0
"$PY" -m unittest discover -s tests >"$logdir/unittest.log" 2>&1 || code=$?
ran="$(grep -o '^Ran [0-9]*' "$logdir/unittest.log" | grep -o '[0-9]*' || echo 0)"
failed="$(grep -o 'failures=[0-9]*\|errors=[0-9]*' "$logdir/unittest.log" \
  | cut -d= -f2 | awk '{s += $1} END {print s + 0}' || true)"
skipped="$(grep -o 'skipped=[0-9]*' "$logdir/unittest.log" | cut -d= -f2 || echo 0)"
if [ "$code" != "0" ]; then
  echo "---- python-tests (exit $code) ----"
  tail -40 "$logdir/unittest.log"
fi
record "python-tests (ran)" "${ran:-0}" "${failed:-0}" "skipped=${skipped:-0}" "$code"

# 2. R unit tests, only where R and the setup's packages exist.
has_r=0
if command -v Rscript >/dev/null 2>&1 && Rscript -e \
    'ok <- all(vapply(c("ggplot2", "knitr", "yaml"), requireNamespace, logical(1), quietly = TRUE)); quit(status = if (ok) 0 else 1)' \
    >/dev/null 2>&1; then
  has_r=1
fi
if [ "$has_r" = "1" ]; then
  code=0
  Rscript tests/test_setup_r.R >"$logdir/r.log" 2>&1 || code=$?
  passed="$(grep -o 'passed: [0-9]*' "$logdir/r.log" | grep -o '[0-9]*' || echo 0)"
  if [ "$code" != "0" ]; then
    echo "---- r-tests (exit $code) ----"
    tail -20 "$logdir/r.log"
  fi
  record "r-tests (passed)" "${passed:-0}" "$([ "$code" = 0 ] && echo 0 || echo 1)" "0" "$code"
else
  echo "SKIPPED-NO-R: Rscript or its packages (ggplot2, knitr, yaml) not found, R unit tests not run."
  record "r-tests" "SKIPPED-NO-R" "0" "0" "skipped"
fi

# Content to check.
if [ "$changed" = "1" ]; then
  # A read loop, not mapfile, so this runs on the bash 3.2 that ships with macOS.
  content=()
  while IFS= read -r f; do
    [ -n "$f" ] && content+=("$f")
  done < <(git diff --name-only --diff-filter=ACMR main -- '*.qmd' '*.md' | grep -v '^tests/fixtures/' || true)
  if [ "${#content[@]}" -eq 0 ]; then
    echo "No .qmd or .md files changed against main. Content checks skipped."
    for name in register prose absence synthesis captions; do
      record "$name" "0" "0" "0" "skipped"
    done
  fi
  qmd=()
  for f in ${content[@]+"${content[@]}"}; do
    case "$f" in *.qmd) qmd+=("$f") ;; esac
  done
  reg_paths=(${qmd[@]+"${qmd[@]}"})
  prose_paths=(${content[@]+"${content[@]}"})
  qmd_paths=(${qmd[@]+"${qmd[@]}"})
else
  content=(.)
  reg_paths=(chapters gallery)
  prose_paths=(.)
  qmd_paths=(chapters reference gallery)
fi

synth=()
for f in chapters/90-interpretation.qmd gallery/g10-interpretation.qmd; do
  [ -f "$f" ] && synth+=("$f")
done

if [ "${#content[@]}" -gt 0 ]; then
  if [ "${#reg_paths[@]}" -gt 0 ]; then
    run_check register "$PY" "$TOOLS/register_guard.py" --strict ${reg_paths[@]+"${reg_paths[@]}"}
    run_check absence "$PY" "$TOOLS/absence_guard.py" ${qmd_paths[@]+"${qmd_paths[@]}"}
    run_check captions "$PY" "$TOOLS/caption_check.py" ${qmd_paths[@]+"${qmd_paths[@]}"}
  else
    for name in register absence captions; do record "$name" "0" "0" "0" "skipped"; done
  fi
  run_check prose "$PY" "$TOOLS/prose_lint.py" ${prose_paths[@]+"${prose_paths[@]}"}
  run_check synthesis "$PY" "$TOOLS/synthesis_check.py" ${synth[@]+"${synth[@]}"}
fi

echo
# "examined" is files for a check, tests for a test suite.
printf '%-22s %14s %7s %10s %8s\n' "check" "examined" "errors" "warnings" "exit"
printf '%-22s %14s %7s %10s %8s\n' "-----" "--------" "------" "--------" "----"
for row in "${rows[@]}"; do
  IFS='|' read -r n e r w c <<<"$row"
  printf '%-22s %14s %7s %10s %8s\n' "$n" "$e" "$r" "$w" "$c"
done
echo
if [ "$status" = "0" ]; then
  echo "check_style: PASS"
else
  echo "check_style: FAIL"
fi
exit "$status"
