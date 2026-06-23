# Runtime Boot Status Window

This example renders the bounded first-boot JSON produced by `velvet-runtime`.

It is intentionally display-only. The window does not import Runtime internals, send commands, restart services, change policy, or touch hardware.

## Install Qt support

```bash
pip install -e .[qt]
```

## Run against the development snapshot

From the Runtime checkout, first create the snapshot:

```bash
bash scripts/up2_first_run.sh
```

Then run the Interface window from the Interface checkout:

```bash
python examples/runtime_boot_window.py \
  --snapshot /path/to/velvet-runtime/.velvet-dev/first-boot-snapshot.json
```

For a deployed UP² snapshot, set:

```bash
export VELVET_BOOT_SNAPSHOT_PATH=/opt/velvet/state/interface/first-boot-snapshot.json
python examples/runtime_boot_window.py
```

Closing this window closes only the Interface process. Runtime continues independently.

The visible states are derived only from the snapshot:

- continuity status
- Court readiness
- Runtime service state
- read-only route count when supplied
- physical control, always displayed as disabled in this first surface
- exact startup failure reason when present
