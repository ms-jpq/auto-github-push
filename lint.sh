#!/usr/bin/env bash

set -eu
set -o pipefail


cd "$(dirname "$0")" || exit 1

FILES=(
  agp.py
  agp/*.py
  )

mypy --ignore-missing-imports -- "${FILES[@]}"
