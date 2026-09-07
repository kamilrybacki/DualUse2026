#!/usr/bin/env bash
# Validate schemas/extraction.gbnf with llama.cpp's own grammar engine (no model needed):
# every fixture's expected object (in grammar key order) must be accepted, three hand-made
# invalid objects must be rejected. Proven 2026-09-07 against llama.cpp master.
#
#   LLAMA_CPP_DIR=/path/to/llama.cpp tools/check_gbnf.sh
#
# Build the validator once:  cmake -B build -DLLAMA_BUILD_TESTS=ON && cmake --build build --target test-gbnf-validator
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LLAMA="${LLAMA_CPP_DIR:-$ROOT/cache/llama.cpp}"
V="$(find "$LLAMA/build" -type f -perm -u+x -name test-gbnf-validator 2>/dev/null | head -1 || true)"
if [[ -z "$V" ]]; then
  echo "test-gbnf-validator not found under $LLAMA/build — set LLAMA_CPP_DIR or build it" >&2
  exit 2
fi
GBNF="$ROOT/schemas/extraction.gbnf"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
ORDER='["event_type","warning_id","agency","issued_at","valid_from","valid_to","location_name","geometry","entities"]'
fail=0

verdict() { "$V" "$GBNF" "$1" 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -o "Input string is [a-z]*" | awk '{print $4}'; }

for f in "$ROOT"/schemas/fixtures/*.json; do
  python3 -c "
import json,sys; e=json.load(open('$f'))['expected']; o=$ORDER
sys.stdout.write(json.dumps({k:e[k] for k in o}, ensure_ascii=False))" > "$TMP/pos.json"
  r="$(verdict "$TMP/pos.json")"
  printf "%-42s %s\n" "$(basename "$f" .json)" "$r"
  [[ "$r" == "valid" ]] || fail=1
done

printf '%s' '{"event_type":"WRECK","warning_id":null,"agency":null,"issued_at":null,"valid_from":null,"valid_to":null,"location_name":null,"geometry":null,"entities":[],"confidence":0.9}' > "$TMP/n1.json"
printf '%s' '{"event_type":"STORM","warning_id":null,"agency":null,"issued_at":null,"valid_from":null,"valid_to":null,"location_name":null,"geometry":null,"entities":[]}' > "$TMP/n2.json"
printf '%s' '{"event_type":"WRECK","warning_id":null,"agency":null,"issued_at":"2026-09-07 12:30","valid_from":null,"valid_to":null,"location_name":null,"geometry":null,"entities":[]}' > "$TMP/n3.json"
for n in 1 2 3; do
  r="$(verdict "$TMP/n$n.json")"
  printf "%-42s %s\n" "negative $n (extra field / bad enum / bad time)" "$r"
  [[ "$r" == "invalid" ]] || fail=1
done
[[ $fail -eq 0 ]] && echo "GBNF OK" || { echo "GBNF CHECK FAILED"; exit 1; }
