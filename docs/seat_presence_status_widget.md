# Seat presence status widget

Surface Studio widget ID:

```text
seat_presence_status
```

The widget reads only Runtime's bounded body-state snapshot and aggregates all
`seat_presence_radar` SensorPacket records. Each seat keeps its own node identity,
freshness, state, movement class, and approximate radar distance.

Displayed states include:

```text
RADAR_PRESENT
NO_RADAR_PRESENCE
DEGRADED
STALE
FAILED
```

`NO_RADAR_PRESENCE` deliberately does not say `EMPTY`. The widget rejects any
packet that claims no detection proves an empty seat, infers occupant identity,
claims heartbeat or medical state, declares an emergency, or grants authority.

One failed seat node does not erase healthy evidence from another seat. Duplicate
seat identities or contradictory movement summaries make the whole projection
fail closed rather than silently choosing one record.

The widget has no serial device, sensor configuration, raw radar frame, Runtime
route, Court grant, executor, or actuation access.
