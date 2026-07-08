#!/usr/bin/env bash
set -e

PYPROJECT_TOML=$(realpath "$(dirname "${BASH_SOURCE[0]}")/../pyproject.toml")
PYTHON_EXEC=$(which python3)

TESTS_SUCCESSFUL=0
TESTS_PERFORMED=0
TESTS_SKIPPED=0
TESTS_FAILED=0

test-galatea-tar-gz(){
  local TARGZ=$1
  local TEST_PATH=$2
  local RC=0

  local expected_version

  tar -xzf "$TARGZ" -C "$TEST_PATH"

  echo 'TEST: Galatea has a version'
  if test-galatea-can-run-version "$TEST_PATH/galatea/galatea/galatea"; then
    ((TESTS_PERFORMED++))
    ((TESTS_SUCCESSFUL++))
    echo 'TEST: Galatea has a version - success'
  else
    ((TESTS_PERFORMED++))
    ((TESTS_FAILED++))
    echo 'TEST: Galatea has a version - failed'
    RC=1
  fi

  if [[ -f "$PYTHON_EXEC" ]]; then
    echo 'TEST: Galatea cli matched expected version'
    expected_version=$("$PYTHON_EXEC" -c "import tomllib; print(tomllib.load(open('$PYPROJECT_TOML', 'rb'))['project']['version'])")
    if [ $? -eq 0 ]; then
      if test-galatea-version-matches "$TEST_PATH/galatea/galatea/galatea" "galatea $expected_version"; then
        ((TESTS_PERFORMED++))
        ((TESTS_SUCCESSFUL++))
        echo 'TEST: Galatea cli matched expected version - success'
      else
        ((TESTS_PERFORMED++))
        ((TESTS_FAILED++))
        echo 'TEST: Galatea cli matched expected version - failed'
        RC=1
      fi

      echo 'TEST: Galatea gui matched expected version'
      if test-galatea-version-matches "$TEST_PATH/galatea/galatea/galatea-gui" "galatea-gui $expected_version"; then
        ((TESTS_PERFORMED++))
        ((TESTS_SUCCESSFUL++))
        echo 'TEST: Galatea gui matched expected version - success'
      else
        ((TESTS_PERFORMED++))
        ((TESTS_FAILED++))
        echo 'TEST: Galatea gui matched expected version - failed'
        RC=1
      fi
    else
      echo "TEST: Galatea cli matched expected version - Skipped. Reason: Unable to get version from $PYPROJECT_TOML."
      ((TESTS_SKIPPED++))
      echo "TEST: Galatea gui matched expected version - Skipped. Reason: Unable to get version from $PYPROJECT_TOML."
      ((TESTS_SKIPPED++))
    fi
  else

    echo "TEST: Galatea cli matched expected version - Skipped. Reason: Python not found."
    ((TESTS_SKIPPED++))

    echo "TEST: Galatea gui matched expected version - Skipped. Reason: Python not found."
    ((TESTS_SKIPPED++))

    return 1
  fi

  echo ""
  echo "Number of tests performed: $TESTS_PERFORMED"
  echo "Number of tests succeed:   $TESTS_SUCCESSFUL"
  echo "Number of tests failed:    $TESTS_FAILED"
  echo "Number of tests skipped:   $TESTS_SKIPPED"
  return $RC
}

test-galatea-can-run-version(){
  local GALATEA_EXEC=$1
  local GALATEA_STDERR
  if [[ ! -f "$GALATEA_EXEC" ]]; then
    echo "Error: $GALATEA_EXEC does not exist or is not a file."
    return 1
  fi

  GALATEA_STDERR=$(mktemp)
  if "$GALATEA_EXEC" --version > /dev//null 2> "$GALATEA_STDERR"; then
    if [[ ! -f "$GALATEA_STDERR" ]]; then
      rm "$GALATEA_STDERR"
    fi
    return 0
  else
    cat "$GALATEA_STDERR"
    rm "$GALATEA_STDERR"
    return 1
  fi
}

test-galatea-version-matches(){
  local GALATEA_EXEC=$1
  local EXPECTED=$2
  local app_version
  if [[ ! -f "$GALATEA_EXEC" ]]; then
    echo "Error: $GALATEA_EXEC does not exist or is not a file."
    return 1
  fi

  app_version=$("$GALATEA_EXEC" --version)
  if [[ "$app_version" == "$EXPECTED" ]]; then
    return 0
  else
    echo "Error: version mismatch. $GALATEA_EXEC: $app_version (expected: $EXPECTED)"
    return 1
  fi
}


usage() {
  cat <<EOF
Usage: $0 [OPTIONS] DNG_FILE

Positional arguments:
  TARGZ_FILE              Path to the required .tar.gz file

Options (optional):
  --test-path PATH        Set a testing/workspace path

  -h, --help              Show this help message and exit

Examples:
  $0 /tmp/image.tar.gz
  $0 --test-path=/tmp/work /tmp/image.tar.gz
  $0 --test-path /tmp/work /tmp/image.tar.gz
  $0 test-path=/tmp/work /tmp/image.tar.gz
EOF
}

# Defaults
TEST_PATH=""
TARGZ_FILE=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --test-path=*)
      TEST_PATH="${1#*=}"
      shift
      ;;
    --test-path)
      if [[ $# -lt 2 ]]; then
        echo "Error: --test-path requires an argument." >&2
        usage
        exit 2
      fi
      TEST_PATH="$2"
      shift 2
      ;;
    test-path=*)
      TEST_PATH="${1#*=}"
      shift
      ;;
    --) # end of options
      shift
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage
      exit 3
      ;;
    *)
      # first non-option is the tar.gz file (required)
      if [[ -z "$TARGZ_FILE" ]]; then
        TARGZ_FILE="$1"
        shift
      else
        echo "Unexpected positional argument: $1" >&2
        usage
        exit 4
      fi
      ;;
  esac
done

# If there are any remaining positional args after parsing, treat the first as tar.gz if not set
if [[ -z "$TARGZ_FILE" && $# -gt 0 ]]; then
  TARGZ_FILE="$1"
  shift
fi

# Validate required tar.gz file
if [[ -z "$TARGZ_FILE" ]]; then
  echo "Error: TARGZ_FILE is required." >&2
  usage
  exit 5
fi

# Optional: verify file exists (comment out if you don't want this check)
if [[ ! -e "$TARGZ_FILE" ]]; then
  echo "Warning: tar.gz file '$TARGZ_FILE' does not exist (or path is wrong)." >&2
  # not exiting; keep as warning. If you prefer to enforce existence, change to exit 6
fi

# Output parsed values (for consumers or testing)
echo "TARGZ_FILE='$TARGZ_FILE'"
if [[ -n "$TEST_PATH" ]]; then
  echo "TEST_PATH='$TEST_PATH'"
fi


if [ -z "$TEST_PATH" ]; then
  TEST_PATH=$(mktemp -d /tmp/galatea.XXXX)
  trap 'rm -rf $TEST_PATH -v' EXIT
fi

if [ ! -d "$TEST_PATH" ]; then
  echo "$TEST_PATH does not exist"
  exit 1
fi

echo "using test path: $TEST_PATH"

test-galatea-tar-gz "$TARGZ_FILE" "$TEST_PATH"
status=$?
if [ "$status" -eq 0 ]; then
  echo "Testing $TARGZ_FILE - success"
else
  echo "Testing $TARGZ_FILE - failed"
fi
exit $status
