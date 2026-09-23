# Founder Climate live status

The Founder Climate room places the trusted widget ID:

```text
climate_environment_status
```

The widget reads only the standard Runtime body-state snapshot and looks for the
`environmental_conditions` SensorPacket published by the `environmental-sensors`
module. It displays genuine evidence when available:

- cabin temperature
- outside temperature when supplied
- relative humidity when supplied
- ambient light
- freshness and health state
- the owning handmaiden, normally Jade

Missing, stale, malformed, or failed evidence is shown explicitly. The widget
does not synthesize healthy values.

## Authority boundary

The environmental packet must remain read-only and must explicitly carry:

```text
read_only: true
grants_authority: false
control_requested: false
```

Any contrary claim fails the projection closed.

The widget is mouse-transparent and does not replace the Climate room's mapped
touchpoints. Existing central-unit, gauges/valves, overview, ventilation, mat,
and staircase touchpoints remain presentation events only.

No HVAC request, Peltier command, fan command, seat-heater command, Runtime route,
Court grant, hardware handle, relay action, CAN transmission, or other actuation
is introduced here. Climate control remains a separate future authority-bearing
contract.

## Body snapshot path

The trusted built-in registry uses:

```text
VELVET_BODY_SNAPSHOT_PATH
```

when set, otherwise it keeps the deployed default:

```text
/run/velvet/body-state.json
```

This matches the rest of the Founder body-evidence widgets and preserves the
fail-closed behavior when no producer has published environmental evidence yet.
