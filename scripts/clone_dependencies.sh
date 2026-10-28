#!/usr/bin/env bash
set -euo pipefail

# Clone or update standalone dependencies for harness2 without git submodules.
# Usage:
#   scripts/clone_dependencies.sh [--dry-run] [-j|--jobs N] [dependency_name]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEPENDENCIES_DIR="${ROOT_DIR}/dependencies"

DRY_RUN=false
JOBS=8
TARGET_DEP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -j|--jobs)
            if [[ $# -lt 2 || ! "$2" =~ ^[0-9]+$ || "$2" -le 0 ]]; then
                echo "Error: $1 requires a positive integer argument" >&2
                exit 1
            fi
            JOBS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--dry-run] [-j|--jobs N] [dependency_name]"
            echo ""
            echo "Options:"
            echo "  --dry-run      Print planned clone / fetch operations without executing"
            echo "  -j, --jobs N   Number of parallel clone/fetch jobs (default: 8)"
            echo "  [name]         Target specific dependency (e.g. autopenbench, workbuddy-bench)"
            exit 0
            ;;
        *)
            if [[ -z "$TARGET_DEP" ]]; then
                TARGET_DEP="$1"
                shift
            else
                echo "Error: Unknown argument '$1'" >&2
                exit 1
            fi
            ;;
    esac
done

# Format: name|origin_url|pin_or_branch
DEPS=(
    "job-bench-eval|https://github.com/Job-Bench/job-bench-eval.git|fa03a17f9ff662f136798a274e10011c3aa00fd0"
    "workbuddy-bench|https://github.com/nguyenthdat/workbuddy-bench.git|625b2233093ae4f23e76be28c1f341d41cc70373"
    "harvey-labs|https://github.com/harveyai/harvey-labs.git|b58a28ae9fde5ee4b810e53b4fd0a1915325a35d"
    "opencode|https://github.com/anomalyco/opencode.git|23fb5e0516c99ac04a1aa46c193efda2e1b9bb24"
    "cybench|https://github.com/andyzorigin/cybench.git|ca483c6443f17a20ba7d6bac3d274859a1721e51"
    "cve-bench|https://github.com/uiuc-kang-lab/cve-bench.git|9fb3e068f260b00dd899ef87951b88e9c60061f1"
    "Rust-SWE-Bench|https://github.com/GhabiX/Rust-SWE-Bench.git|6275b18be51ce3242de9e959a32260dd59909595"
    "CRUST-bench|https://github.com/anirudhkhatry/CRUST-bench.git|4b4702544b800a3821feea128c5b9e413665dc83"
    "AgentRE-Bench|https://github.com/agentrebench/AgentRE-Bench.git|654c4042bb0022b32b522769d99f76b103f5d504"
    "BinaryAudit|https://github.com/QuesmaOrg/BinaryAudit.git|175b7ec1a39b7ba1545ae008a9e93106348c3b4e"
    "autopenbench|https://github.com/nguyenthdat/auto-pen-bench.git|9c4890a7195896a399339f4b1b0e0c498fdd27cb"
    "bountybench|https://github.com/nguyenthdat/bountybench.git|8ece6aab0b954f7c85b5705e69f0142eeaf2c5d1"
    "hptsa|https://github.com/nguyenthdat/HPTSA.git|ab4c77ce0ecd44fa9f1b9adc82779312342d9a2e"
    "hackworld|https://github.com/nguyenthdat/HackWorld.git|7eddbe396d2adb3042482134fd08508e8ea21a3f"
    "nyu-ctf-bench|https://github.com/nguyenthdat/NYU_CTF_Bench.git|4c5744f55a31a58e03d6118c9dbb1c18e5bbdfa9"
    "intercode|https://github.com/nguyenthdat/intercode.git|c3e46d827cfc9d4c704ec078f7abf9f41e3191d8"
    "xbow-validation|https://github.com/nguyenthdat/validation-benchmarks.git|a16cb1ba0701b20d63913846536fc7b0672082af"
    "maleval|https://github.com/nguyenthdat/MalEval.git|c906fa1e83d89c5f2473f9ef4f93320382cae3df"
    "droidbench|https://github.com/nguyenthdat/DroidBench.git|a57fa6f42f278591695672f1aa8b37c275139370"
    "ghera|https://github.com/nguyenthdat/android-app-vulnerability-benchmarks.git|31dc21e922ecd327b6ec90a10a507aac7f813700"
    "mobilecybench|https://github.com/nguyenthdat/mobilecybench.git|d196c46fb23d9f6ad6391819ea62d025e1b29693"
    "mas-crackmes|https://github.com/nguyenthdat/mas-crackmes.git|d27a4857b79289cdd88fda423f519f8cd4c42db1"
    "mastg|https://github.com/nguyenthdat/mastg.git|8bee312ba8fa45f7d617f0d806ac14920f2ad3d0"
    "cybergym|https://github.com/nguyenthdat/cybergym.git|c6fe2027d39471375920b92cf1025e23a99ffda5"
    "cybergym-e2e|https://github.com/nguyenthdat/cybergym-e2e.git|d0ae0f02e76ebc084389bf21e755f4b41ac9765a"
    "fuzzingbrain-bench|https://github.com/nguyenthdat/FuzzingBrain-Bench.git|6010bb4f98524157a13a2a68c3b6921d44c7f830"
    "crsbench|https://github.com/nguyenthdat/CRSBench.git|b4ec940f93ab531d70425cd274696651a84bf5e8"
    "oss-crs|https://github.com/nguyenthdat/oss-crs.git|69cbcb6981f212fc125c7022eda880b4fdad02ce"
    "sec-bench|https://github.com/nguyenthdat/SEC-bench.git|31eb43485a3de47da260be0f978528b1f2314415"
    "sec-bench-pro|https://github.com/nguyenthdat/SEC-bench-Pro.git|da80928ee20dc417ca6a068a1213e1d9d279df20"
    "calif-publications|https://github.com/nguyenthdat/publications.git|0a1c715b06477a32155329bd0c535f30c91bdabf"
    "CyberSOCEval_data|https://github.com/CrowdStrike/CyberSOCEval_data.git|ce7daa5bc7da51559ca97476d2277be02631783e"
)

mkdir -p "${DEPENDENCIES_DIR}"

sync_dep() {
    local name="$1"
    local url="$2"
    local pin="$3"
    local dest="${DEPENDENCIES_DIR}/${name}"

    if [[ -d "$dest/.git" || -f "$dest/.git" ]]; then
        local current_head
        current_head="$(git -C "$dest" rev-parse HEAD 2>/dev/null || true)"
        if [[ "$current_head" == "$pin" ]]; then
            echo "[UP-TO-DATE] ${name} (${pin:0:8})"
            return 0
        fi

        echo "[UPDATE] ${name} (${dest})"
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "  (dry-run) git -C '${dest}' fetch origin"
            echo "  (dry-run) git -C '${dest}' checkout '${pin}'"
        else
            local current_remote
            current_remote="$(git -C "$dest" remote get-url origin 2>/dev/null || true)"
            if [[ -n "$current_remote" && "$current_remote" != "$url" ]]; then
                echo "  Updating origin URL: ${current_remote} -> ${url}"
                git -C "$dest" remote set-url origin "$url"
            fi
            git -C "$dest" fetch origin --quiet || git -C "$dest" fetch origin
            git -C "$dest" checkout "$pin" --quiet || git -C "$dest" checkout "$pin"
        fi
    elif [[ -d "$dest" ]]; then
        if [[ -z "$(ls -A "$dest" 2>/dev/null || true)" ]]; then
            echo "[CLONE] ${name} from ${url} (into empty directory ${dest})"
            if [[ "$DRY_RUN" == "true" ]]; then
                echo "  (dry-run) git clone '${url}' '${dest}'"
                echo "  (dry-run) git -C '${dest}' checkout '${pin}'"
            else
                git clone "$url" "$dest"
                git -C "$dest" checkout "$pin" --quiet || git -C "$dest" checkout "$pin"
            fi
        else
            echo "[EXISTS] ${name} at ${dest} (non-empty directory without .git, skipping)"
        fi
    else
        echo "[CLONE] ${name} from ${url}"
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "  (dry-run) git clone '${url}' '${dest}'"
            echo "  (dry-run) git -C '${dest}' checkout '${pin}'"
        else
            git clone "$url" "$dest"
            git -C "$dest" checkout "$pin" --quiet || git -C "$dest" checkout "$pin"
        fi
    fi
}

matched=0
declare -a target_entries=()

for entry in "${DEPS[@]}"; do
    IFS="|" read -r name url pin <<< "$entry"
    if [[ -n "$TARGET_DEP" && "$TARGET_DEP" != "$name" ]]; then
        continue
    fi
    matched=$((matched + 1))
    target_entries+=("$entry")
done

if [[ $matched -eq 0 && -n "$TARGET_DEP" ]]; then
    echo "Error: Unknown dependency '${TARGET_DEP}'" >&2
    echo "Available dependencies:"
    for entry in "${DEPS[@]}"; do
        IFS="|" read -r name _ _ <<< "$entry"
        echo "  - $name"
    done
    exit 1
fi

running=0
failed=0

for entry in "${target_entries[@]}"; do
    IFS="|" read -r name url pin <<< "$entry"

    if [[ "$DRY_RUN" == "true" || "$JOBS" -le 1 ]]; then
        sync_dep "$name" "$url" "$pin" || failed=1
    else
        sync_dep "$name" "$url" "$pin" &
        running=$((running + 1))
        if [[ $running -ge $JOBS ]]; then
            wait -n || failed=1
            running=$((running - 1))
        fi
    fi
done

while [[ $running -gt 0 ]]; do
    wait -n || failed=1
    running=$((running - 1))
done

if [[ $failed -ne 0 ]]; then
    echo "Error: One or more dependency operations failed." >&2
    exit 1
fi

echo "Done."
