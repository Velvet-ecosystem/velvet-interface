# Founder Development Launcher

The full Founder Interface and Runtime are separate processes. Production uses the stable `/run/velvet` IPC paths, while repo-local development Runtime state lives under `velvet-runtime/.velvet-dev`.

Use the development launcher when testing both checkouts together:

```bash
bash scripts/run_founder_dev.sh
```

With the standard sibling checkout layout, it binds Interface to:

```text
../velvet-runtime/.velvet-dev/first-boot-snapshot.json
../velvet-runtime/.velvet-dev/run/conversation.sock
```

It also defaults this presentation marker:

```text
VELVET_INTERFACE_DEVELOPMENT=true
```

That marker is used only to label development surfaces clearly. It does not grant or suppress Runtime, Court, maintenance, owner-presence, or hardware authority. An explicit caller value is preserved.

This prevents the Founder UI from accidentally looking for its boot evidence inside `velvet-interface/.velvet-dev` or trying the deployed conversation socket while Runtime is using its repo-local development socket.

For a non-sibling workspace, set the Runtime checkout explicitly:

```bash
export VELVET_RUNTIME_ROOT=/path/to/velvet-runtime
bash scripts/run_founder_dev.sh
```

Existing explicit path overrides remain authoritative:

```text
VELVET_BOOT_SNAPSHOT_PATH
VELVET_CONVERSATION_SOCKET_PATH
VELVET_INTERFACE_DEVELOPMENT
```

Additional Founder launcher arguments pass through unchanged, for example:

```bash
bash scripts/run_founder_dev.sh \
  --width 1152 \
  --height 648 \
  --initial forge \
  --placement-debug
```

## Identity and authority

The helper does not set owner presence, maintenance access, physical authority, or actuation state. Those boundaries remain independent. `VELVET_OWNER_PRESENT` and `VELVET_MAINTENANCE_UNLOCKED` must still be supplied through their existing trusted commissioning flow.

The development presentation marker likewise does not create a privileged mode. Founder Forge workspaces may read canonical evidence while still showing `PRESENTATION AUTHORITY ONLY` and `PHYSICAL EXECUTION DISABLED`.

## Body-state evidence

This helper intentionally does not invent or relocate body-state evidence. `VELVET_BODY_SNAPSHOT_PATH` keeps its existing launcher/deployment behavior. Until a Runtime body producer publishes a valid snapshot, the Founder Body widget remains `UNAVAILABLE` rather than fabricating healthy sensor state.
