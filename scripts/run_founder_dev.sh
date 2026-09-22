#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Launch Founder Interface against a sibling/local Runtime development state.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${VELVET_INTERFACE_PYTHON:-python3}"
RUNTIME_ROOT="${VELVET_RUNTIME_ROOT:-${REPO_ROOT}/../velvet-runtime}"

if [[ ! -d "${RUNTIME_ROOT}" ]]; then
  echo "[VELVET FOUNDER] Runtime checkout not found: ${RUNTIME_ROOT}" >&2
  echo "[VELVET FOUNDER] Set VELVET_RUNTIME_ROOT to the velvet-runtime checkout." >&2
  exit 2
fi

RUNTIME_ROOT="$(cd -- "${RUNTIME_ROOT}" && pwd)"
RUNTIME_DEV_ROOT="${RUNTIME_ROOT}/.velvet-dev"

export VELVET_BOOT_SNAPSHOT_PATH="${VELVET_BOOT_SNAPSHOT_PATH:-${RUNTIME_DEV_ROOT}/first-boot-snapshot.json}"
export VELVET_CONVERSATION_SOCKET_PATH="${VELVET_CONVERSATION_SOCKET_PATH:-${RUNTIME_DEV_ROOT}/run/conversation.sock}"
export PYTHONPATH="${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

if [[ ! -f "${VELVET_BOOT_SNAPSHOT_PATH}" ]]; then
  echo "[VELVET FOUNDER] Runtime boot snapshot is not present yet: ${VELVET_BOOT_SNAPSHOT_PATH}" >&2
  echo "[VELVET FOUNDER] Interface will remain fail-closed until Runtime evidence exists." >&2
fi

cd "${REPO_ROOT}"
exec "${PYTHON_BIN}" -m velvet_interface.founder_surface_launcher "$@"
