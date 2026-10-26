#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------
# Environment & Repo Root Setup
# ---------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Autoload .env if present without overwriting existing environment variables
if [ -f "${REPO_ROOT}/.env" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    # Trim leading/trailing whitespace
    trimmed="${line#"${line%%[![:space:]]*}"}"
    trimmed="${trimmed%"${trimmed##*[![:space:]]}"}"
    # Skip comments and empty lines
    if [ -z "$trimmed" ] || [[ "$trimmed" =~ ^# ]]; then
      continue
    fi
    # Match KEY=VALUE or export KEY=VALUE
    if [[ "$trimmed" =~ ^(export[[:space:]]+)?([a-zA-Z_][a-zA-Z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[2]}"
      val="${BASH_REMATCH[3]}"
      # Remove surrounding quotes if present (double or single quotes)
      if [[ "$val" =~ ^\"(.*)\"$ ]]; then
        val="${BASH_REMATCH[1]}"
      elif [[ "$val" =~ ^\'(.*)\'$ ]]; then
        val="${BASH_REMATCH[1]}"
      fi
      # Only export if not already set in the environment
      if [ -z "${!key+x}" ]; then
        export "$key"="$val"
      fi
    fi
  done < "${REPO_ROOT}/.env"
fi

# Sanitize trailing slashes from key path variables if defined
if [ -n "${GHIDRA_INSTALL_DIR:-}" ]; then
  GHIDRA_INSTALL_DIR="${GHIDRA_INSTALL_DIR%/}"
fi
if [ -n "${JAVA_HOME:-}" ]; then
  JAVA_HOME="${JAVA_HOME%/}"
fi

# Detect OS and Architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

# ---------------------------------------------------------
# JAVA_HOME Detection
# ---------------------------------------------------------
if [ -n "${JAVA_HOME:-}" ] && [ -d "$JAVA_HOME" ]; then
  export JAVA_HOME
else
  unset JAVA_HOME 2>/dev/null || true
  DETECTED_JAVA=""

  if [ "$OS" = "Darwin" ]; then
    # 1. Try /usr/libexec/java_home with 21+ or standard
    if [ -x "/usr/libexec/java_home" ]; then
      DETECTED_JAVA="$(/usr/libexec/java_home -v 21+ 2>/dev/null || /usr/libexec/java_home 2>/dev/null || true)"
    fi
    # 2. Check Homebrew, SDKMAN, and standard macOS JVM directories
    if [ -z "$DETECTED_JAVA" ] || [ ! -d "$DETECTED_JAVA" ]; then
      for candidate in \
        /opt/homebrew/opt/openjdk* \
        /usr/local/opt/openjdk* \
        "$HOME"/.sdkman/candidates/java/* \
        /Library/Java/JavaVirtualMachines/*/Contents/Home \
        "$HOME"/Library/Java/JavaVirtualMachines/*/Contents/Home; do
        if [ -d "$candidate" ]; then
          DETECTED_JAVA="$candidate"
          break
        fi
      done
    fi
  elif [ "$OS" = "Linux" ]; then
    # Check Linux search paths
    for candidate in \
      /usr/lib/jvm/* \
      "$HOME"/.sdkman/candidates/java/*; do
      if [ -d "$candidate" ]; then
        DETECTED_JAVA="$candidate"
        break
      fi
    done
    # Resolve which java via readlink -f
    if [ -z "$DETECTED_JAVA" ] || [ ! -d "$DETECTED_JAVA" ]; then
      if command -v java >/dev/null 2>&1; then
        JAVA_BIN="$(which java)"
        if command -v readlink >/dev/null 2>&1; then
          RESOLVED_JAVA="$(readlink -f "$JAVA_BIN" 2>/dev/null || true)"
          if [ -n "$RESOLVED_JAVA" ]; then
            DETECTED_JAVA="$(dirname "$(dirname "$RESOLVED_JAVA")")"
          fi
        fi
      fi
    fi
  fi

  if [ -n "$DETECTED_JAVA" ] && [ -d "$DETECTED_JAVA" ]; then
    export JAVA_HOME="${DETECTED_JAVA%/}"
  fi
fi

# ---------------------------------------------------------
# GHIDRA_INSTALL_DIR Detection
# ---------------------------------------------------------
GHIDRA_VALID=0
if [ -n "${GHIDRA_INSTALL_DIR:-}" ]; then
  if [ -f "${GHIDRA_INSTALL_DIR}/Ghidra/application.properties" ]; then
    export GHIDRA_INSTALL_DIR
    GHIDRA_VALID=1
  elif [ -f "${GHIDRA_INSTALL_DIR}/libexec/Ghidra/application.properties" ]; then
    export GHIDRA_INSTALL_DIR="${GHIDRA_INSTALL_DIR}/libexec"
    GHIDRA_VALID=1
  fi
fi

if [ "$GHIDRA_VALID" -eq 0 ]; then
  unset GHIDRA_INSTALL_DIR 2>/dev/null || true
  DETECTED_GHIDRA=""

  if [ "$OS" = "Darwin" ]; then
    GHIDRA_CANDIDATES=(
      /opt/homebrew/opt/ghidra/libexec
      /usr/local/opt/ghidra/libexec
      /opt/homebrew/opt/ghidra
      /usr/local/opt/ghidra
      /Applications/ghidra*
      /Applications/Ghidra*
      "$HOME"/Applications/ghidra*
      "$HOME"/Applications/Ghidra*
      "$HOME"/ghidra*
      "$HOME"/Ghidra*
    )
  elif [ "$OS" = "Linux" ]; then
    GHIDRA_CANDIDATES=(
      /opt/ghidra*
      /usr/local/ghidra*
      /usr/share/ghidra*
      /opt/homebrew/opt/ghidra/libexec
      "$HOME"/ghidra*
      "$HOME"/Ghidra*
    )
  else
    GHIDRA_CANDIDATES=(
      /opt/ghidra*
      /usr/local/ghidra*
      "$HOME"/ghidra*
      "$HOME"/Ghidra*
    )
  fi

  for candidate in "${GHIDRA_CANDIDATES[@]}"; do
    candidate="${candidate%/}"
    if [ -f "${candidate}/Ghidra/application.properties" ]; then
      DETECTED_GHIDRA="$candidate"
      break
    elif [ -f "${candidate}/libexec/Ghidra/application.properties" ]; then
      DETECTED_GHIDRA="${candidate}/libexec"
      break
    fi
  done

  if [ -n "$DETECTED_GHIDRA" ]; then
    export GHIDRA_INSTALL_DIR="$DETECTED_GHIDRA"
    GHIDRA_VALID=1
  fi
fi

# ---------------------------------------------------------
# REA_JADX_MCP_JAR Detection
# ---------------------------------------------------------
if [ -n "${REA_JADX_MCP_JAR:-}" ] && [ -f "$REA_JADX_MCP_JAR" ]; then
  export REA_JADX_MCP_JAR
else
  unset REA_JADX_MCP_JAR 2>/dev/null || true
  DETECTED_JADX=""

  JADX_CANDIDATES=(
    "$HOME"/.local/opt/jadx*.jar
    "$HOME"/.local/opt/*.jar
    "$HOME"/.local/share/jadx/*.jar
    "$HOME"/.cache/jadx/*.jar
    /opt/homebrew/opt/jadx*/*.jar
    /usr/local/opt/jadx*/*.jar
    /opt/jadx/*.jar
    /usr/local/share/jadx/*.jar
    /usr/share/jadx/*.jar
  )

  for candidate in "${JADX_CANDIDATES[@]}"; do
    if [ -f "$candidate" ]; then
      DETECTED_JADX="$candidate"
      break
    fi
  done

  if [ -n "$DETECTED_JADX" ]; then
    export REA_JADX_MCP_JAR="$DETECTED_JADX"
  fi
fi

# ---------------------------------------------------------
# REA_ANALYSIS_PROVIDER Selection
# ---------------------------------------------------------
if [ -n "${REA_ANALYSIS_PROVIDER:-}" ]; then
  export REA_ANALYSIS_PROVIDER
else
  if [ "$GHIDRA_VALID" -eq 1 ]; then
    export REA_ANALYSIS_PROVIDER="ghidra"
  fi
fi

# ---------------------------------------------------------
# Memory & Timeouts
# ---------------------------------------------------------
export REA_NODE_MAX_OLD_SPACE_MIB="${REA_NODE_MAX_OLD_SPACE_MIB:-4096}"
export REA_GHIDRA_STARTUP_TIMEOUT_MS="${REA_GHIDRA_STARTUP_TIMEOUT_MS:-300000}"
export REA_JADX_HEAP_MIB="${REA_JADX_HEAP_MIB:-4096}"
export REA_JADX_OPERATION_TIMEOUT_MS="${REA_JADX_OPERATION_TIMEOUT_MS:-120000}"
export REA_CAPTURE_DECODER_OLD_GENERATION_MIB="${REA_CAPTURE_DECODER_OLD_GENERATION_MIB:-512}"

# Ensure NODE_OPTIONS contains --max-old-space-size
if [ -z "${NODE_OPTIONS:-}" ]; then
  export NODE_OPTIONS="--max-old-space-size=${REA_NODE_MAX_OLD_SPACE_MIB}"
elif [[ "${NODE_OPTIONS}" != *"--max-old-space-size="* ]]; then
  export NODE_OPTIONS="${NODE_OPTIONS} --max-old-space-size=${REA_NODE_MAX_OLD_SPACE_MIB}"
fi

# ---------------------------------------------------------
# Runner Selection
# ---------------------------------------------------------
REA_VERSION="${REA_VERSION:-6.4.0}"
RUNNER=""
if command -v bun >/dev/null 2>&1; then
  RUNNER="bunx"
elif command -v npx >/dev/null 2>&1; then
  RUNNER="npx"
elif command -v rea >/dev/null 2>&1; then
  RUNNER="rea"
fi

# ---------------------------------------------------------
# Diagnostic Subcommands Check
# ---------------------------------------------------------
if [ $# -gt 0 ] && { [ "$1" = "status" ] || [ "$1" = "check" ] || [ "$1" = "test" ] || [ "$1" = "info" ] || [ "$1" = "--check" ]; }; then
  echo "REA MCP Environment Diagnostic Summary"
  echo "======================================"
  echo "OS:                    ${OS}"
  echo "Architecture:          ${ARCH}"

  if [ -n "${JAVA_HOME:-}" ]; then
    JAVA_VER=""
    if [ -x "${JAVA_HOME}/bin/java" ]; then
      JAVA_VER="$("${JAVA_HOME}/bin/java" -version 2>&1 | awk -F '"' '/version/ {print $2}' | head -n 1)"
    fi
    echo "JAVA_HOME:             ${JAVA_HOME} (java version: ${JAVA_VER:-unknown})"
  else
    echo "JAVA_HOME:             <not set>"
  fi

  if [ -n "${GHIDRA_INSTALL_DIR:-}" ]; then
    GHIDRA_VER=""
    if [ -f "${GHIDRA_INSTALL_DIR}/Ghidra/application.properties" ]; then
      GHIDRA_VER="$(awk -F '=' '/^application\.version=/ {print $2}' "${GHIDRA_INSTALL_DIR}/Ghidra/application.properties" | tr -d '[:space:]')"
    fi
    echo "GHIDRA_INSTALL_DIR:    ${GHIDRA_INSTALL_DIR} (ghidra version: ${GHIDRA_VER:-unknown})"
  else
    echo "GHIDRA_INSTALL_DIR:    <not set>"
  fi

  echo "REA_JADX_MCP_JAR:      ${REA_JADX_MCP_JAR:-<not set>}"
  echo "REA_ANALYSIS_PROVIDER: ${REA_ANALYSIS_PROVIDER:-<not set>}"

  if [ -n "$RUNNER" ]; then
    if [ "$RUNNER" = "bunx" ]; then
      echo "Runner binary:         bunx (bunx rea-agents@${REA_VERSION})"
    elif [ "$RUNNER" = "npx" ]; then
      echo "Runner binary:         npx (npx -y rea-agents@${REA_VERSION})"
    elif [ "$RUNNER" = "rea" ]; then
      echo "Runner binary:         rea (native binary)"
    fi
  else
    echo "Runner binary:         <none found (bun, npx, rea not in PATH)>"
  fi
  exit 0
fi

# ---------------------------------------------------------
# Execution
# ---------------------------------------------------------
# Default command to "mcp" if no arguments provided
if [ $# -eq 0 ]; then
  set -- "mcp"
fi

if [ "$RUNNER" = "bunx" ]; then
  exec bunx "rea-agents@${REA_VERSION}" "$@"
elif [ "$RUNNER" = "npx" ]; then
  exec npx -y "rea-agents@${REA_VERSION}" "$@"
elif [ "$RUNNER" = "rea" ]; then
  exec rea "$@"
else
  echo "Error: Neither bun, npx, nor rea binary was found in PATH." >&2
  exit 1
fi
