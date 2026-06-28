#!/usr/bin/env bash
set -euo pipefail

root="${1:-.}"

if find "$root" -type f \( \
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
\) | grep -q .; then
  echo "Secret-like file name found." >&2
  find "$root" -type f \( \
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
  \) >&2
  exit 1
fi

if rg -n --hidden --glob '!.git/**' \
  '(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----)' \
  "$root"; then
  echo "Secret-looking value found." >&2
  exit 1
fi

echo "secret sanity passed"
