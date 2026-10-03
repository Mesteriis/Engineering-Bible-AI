#!/usr/bin/env bash
set -euo pipefail

root="${1:-.}"
root="$(cd "$root" && pwd)"
allowlist_file="${root}/.secret-sanity-allowlist"

secret_patterns=(
    'sk-[A-Za-z0-9_-]{20,}'
    'ghp_[A-Za-z0-9_]{20,}'
    'github_pat_[A-Za-z0-9_]{20,}'
    'xox[baprs]-[A-Za-z0-9-]{20,}'
    '(?:AKIA|ASIA|AGPA|AIDA|AIPY|AROA|ANPA)[A-Z0-9]{16}'
    'AIza[0-9A-Za-z-_]{35}'
    'glpat-[A-Za-z0-9_-]{20,}'
    'npm_[A-Za-z0-9_-]{20,}'
    'pypi-[A-Za-z0-9_-]{20,}'
    '-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----'
)

secret_regex="(${secret_patterns[0]}"
for idx in "${!secret_patterns[@]}"; do
    if [[ "$idx" -eq 0 ]]; then
        continue
    fi
    secret_regex+="|${secret_patterns[$idx]}"
done
secret_regex+=")"

declare -a allowlist_literals
declare -a allowlist_regex

if [[ -f "$allowlist_file" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        trimmed_line="$(printf '%s' "$line" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
        if [[ -z "$trimmed_line" || "${trimmed_line:0:1}" == "#" ]]; then
            continue
        fi
        if [[ "$trimmed_line" == re:* ]]; then
            allowlist_regex+=("${trimmed_line#re:}")
        else
            allowlist_literals+=("$trimmed_line")
        fi
    done <"$allowlist_file"
fi

is_allowed() {
    local value="$1"

    for literal in "${allowlist_literals[@]}"; do
        if [[ "$value" == *"$literal"* ]]; then
            return 0
        fi
    done

    for expression in "${allowlist_regex[@]}"; do
        if [[ "$value" =~ $expression ]]; then
            return 0
        fi
    done

    return 1
}

if ! secret_file_found="$(find "$root" \( -name .git -o -path "$root/.engineering-bible" \) -prune -o -type f \
    \( \
    -name '.env' -o \
    -name '.env.*' -o \
    -name 'auth.json' -o \
    -name 'config.toml' -o \
    -name 'credentials*.json' -o \
    -name 'token*.json' -o \
    -name '*id_rsa*' -o \
    -name '*id_ed25519*' -o \
    -name '*.pem' -o \
    -name '*.key' -o \
    -name '*.p8' -o \
    -name '*.p12' \
    \) -print | awk 'NR == 1 { found = 1 } END { if (found) print "found" }')"; then
    echo "Secret-like file scan failed." >&2
    exit 1
fi
if [[ -n "$secret_file_found" ]]; then
    echo "Secret-like file name found." >&2
    find "$root" \( -name .git -o -path "$root/.engineering-bible" \) -prune -o -type f \
        \( \
        -name '.env' -o \
        -name '.env.*' -o \
        -name 'auth.json' -o \
        -name 'config.toml' -o \
        -name 'credentials*.json' -o \
        -name 'token*.json' -o \
        -name '*id_rsa*' -o \
        -name '*id_ed25519*' -o \
        -name '*.pem' -o \
        -name '*.key' -o \
        -name '*.p8' -o \
        -name '*.p12' \
        \) -print >&2
    exit 1
fi

if ! command -v rg >/dev/null 2>&1; then
    echo "WARN: rg not found; skipping secret-sanity content scan" >&2
    echo "secret sanity passed"
    exit 0
fi

secret_findings=0
scan_paths_file="$(mktemp "${TMPDIR:-/tmp}/engineering-bible-scan-paths.XXXXXX")" || {
    echo "Secret scan setup failed." >&2
    exit 1
}
rg_output_file="$(mktemp "${TMPDIR:-/tmp}/engineering-bible-rg-output.XXXXXX")" || {
    rm -f -- "$scan_paths_file"
    echo "Secret scan setup failed." >&2
    exit 1
}
trap 'rm -f -- "$scan_paths_file" "$rg_output_file"' EXIT
if ! find "$root" -mindepth 1 -maxdepth 1 \
    ! -path "$root/.engineering-bible" \
    ! -path "$root/.git" \
    -print0 >"$scan_paths_file"; then
    echo "Secret scan path enumeration failed." >&2
    exit 1
fi
declare -a scan_paths=()
while IFS= read -r -d '' path; do
    scan_paths+=("$path")
done <"$scan_paths_file"
if [[ "${#scan_paths[@]}" -eq 0 ]]; then
    echo "secret sanity passed"
    exit 0
fi
if rg -n --hidden --no-ignore \
    --glob '!.git/**' \
    -o "$secret_regex" "${scan_paths[@]}" |
    awk -v max_bytes=8388608 '
        {
            if (!overflow) {
                bytes += length($0) + 1
                if (bytes > max_bytes) {
                    overflow = 1
                } else {
                    print
                }
            }
        }
        END { if (overflow) exit 2 }
    ' >"$rg_output_file"; then
    rg_status=0
else
    rg_status=$?
fi
if [[ "$rg_status" -gt 1 ]]; then
    echo "Secret content scan failed." >&2
    exit 1
fi
while IFS=: read -r file line col match; do
    if is_allowed "$match"; then
        continue
    fi
    secret_findings=$((secret_findings + 1))
    printf '%s:%s:%s: %s\n' "$file" "$line" "$col" "$match" >&2
done <"$rg_output_file"

if [[ "$secret_findings" -ne 0 ]]; then
    echo "Secret-looking value found." >&2
    exit 1
fi

echo "secret sanity passed"
