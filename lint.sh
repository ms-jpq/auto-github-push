#!/usr/bin/env bash

set -eu
set -o pipefail


cd "$(dirname "$0")" || exit 1

FILES=(
  main.py
  agp/*.py
  )

mypy -- "${FILES[@]}"
