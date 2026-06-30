#!/usr/bin/env bash

set -e

FREEZE_SCRIPT=$(dirname "$0")/create_standalone.py

DEFAULT_BUILD_VENV=build/build_standalone_build_env

default_python_path=$(which python3)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

create_standalone(){
    local wheel
    local uv_path
    local python_version
    uv_path=$1
    wheel=$2
    python_version=$3

    tmp_path=$(mktemp -d)
    $uv_path export --python="$python_version" --frozen --no-dev --no-emit-project --no-annotate --group freeze --format pylock.toml --output-file "${tmp_path}/pylock.toml" > /dev/null
    $uv_path run --python="$python_version" "$FREEZE_SCRIPT" --package-manager=uv --include-tab-completions --requirements "${tmp_path}/pylock.toml" "${wheel}" galatea ./contrib/bootstrap_standalone.py
}


create_venv() {
    base_python_path=$1
    venv_path=$2
    $base_python_path -m venv $venv_path
    . $venv_path/bin/activate
    python -m pip install uv
    deactivate
}
# ======

print_usage(){
    echo "Usage: $0 [options] wheel"
}

show_help() {
    print_usage
    echo
    echo "Arguments:"
    echo "  wheel            Python (.whl) Wheel file  to use. "
    echo
    echo "Options:"
    echo "  --python-version=VERSION Python version to use (default: 3.12+gil)"
    echo "  --help           Display this help message and exit."
}

python_version=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --python-version=*)
      python_version="${1#*=}"
      shift
      ;;
    --python-version)
      python_version="$2"
      shift 2
      ;;
    --help|-h)
      show_help
      exit 0
      ;;
    -*)
      echo "Unknown option: $1"
      print_usage
      exit 1
      ;;
    *)
      wheel="$1"
      shift
      break
      ;;
  esac
done

if [ -z "$wheel" ]; then
  echo "Error: Missing wheel argument."
  print_usage
  exit 1
fi

# ======
if ! command -v uv > /dev/null 2>&1
then
    build_venv=$DEFAULT_BUILD_VENV
    python_path=$default_python_path

    create_venv "$python_path" $build_venv
    uv_exec="$build_venv/bin/uv"
else
    uv_exec=$(which uv)
fi

create_standalone "$uv_exec" "$wheel" "$python_version"
