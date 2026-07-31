# Founder Live Refresh

The Founder Runtime window now combines two independent local evidence files:

```text
Runtime boot snapshot
  + Runtime body-state snapshot
  -> FounderLiveStatus
  -> Qt presentation
```

The default paths are:

```text
.velvet-dev/first-boot-snapshot.json
.velvet-dev/body-state.json
```

Production paths may be supplied through command arguments or environment variables:

```text
VELVET_BOOT_SNAPSHOT_PATH
VELVET_BODY_SNAPSHOT_PATH
```

## Launch

```bash
python3 examples/runtime_boot_window.py \
  --snapshot .velvet-dev/first-boot-snapshot.json \
  --body-snapshot .velvet-dev/body-state.json \
  --refresh-ms 1000
```

The refresh interval must remain between 250 and 60000 milliseconds.

## Displayed evidence

The window may show:

- Continuity posture
- Court posture
- Runtime service state
- registered read-only routes
- body presence recommendation
- current sensor count
- current health-record count
- current receipt count
- physical-control posture

The body presence row is a presentation recommendation derived from standard health states, severities, and sensor freshness. It is not proof of authority or execution.

## Failure behavior

The boot and body snapshots are loaded independently. A missing or invalid body snapshot does not crash the Founder surface or invent healthy values. It displays `UNAVAILABLE` and preserves the Runtime boot posture.

The body snapshot must declare:

```text
schema: velvet.runtime.body_state_snapshot.v1
read_only: true
authority: none
actuation_granted: false
actuation_performed: false
```

The contained SensorPacket and HealthEvent records are passed through the same strict `BodyStateStore` used by Diagnostics. Authority-bearing nested fields are rejected.

## Refresh boundary

Qt reloads bounded JSON files with a `QTimer`. Interface receives no Runtime object, Event Bus, CAN handle, executor registry, socket authority, or physical-control capability.

The original one-shot `run_window(BootStatusViewModel)` entry point remains available for compatibility. The command-line entry point uses `run_live_window()`.
