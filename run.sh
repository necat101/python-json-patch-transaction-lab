#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "python not found (tried: python3 python py)" >&2
  exit 1
fi

case "${1:-run}" in
  run|runner|"")
    "$PY" runner.py
    ;;
  test|tests|unittest)
    "$PY" -m unittest test_independent -v
    ;;
  all)
    "$PY" runner.py && "$PY" -m unittest test_independent -q
    ;;
  *)
    echo "usage: $0 [run|test|all]" >&2
    exit 2
    ;;
esac
