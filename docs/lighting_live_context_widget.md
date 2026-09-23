# Founder Lighting live context

The Lighting room uses the trusted widget ID:

```text
lighting_context_status
```

It is a read-only presentation of genuine ambient-light evidence already published by Runtime's reviewed `environmental-sensors` package. The current source is the `ambient_light_lux` field from the standard `environmental_conditions` SensorPacket.

The widget may show:

- environmental health state
- current ambient light in lux
- freshness
- observing handmaiden
- lighting fixture observation state
- physical-control state

## Deliberate boundary

Ambient light is not the same thing as lighting fixture state.

Until a reviewed lighting observer exists, the widget reports fixture evidence as:

```text
UNBOUND
```

It must not infer whether starlight, cabin accents, scene presets, or any lamp is on from ambient lux alone.

Likewise physical control remains:

```text
DISABLED
```

The widget does not expose brightness setters, scene selection, relays, GPIO, CAN, shell, Court grants, Runtime capabilities, or other actuation paths.

## Why this is useful now

The official v0 Lighting sheet calls for starlight, cabin accents, brightness, night mode, and scene presets. Those should eventually be backed by a dedicated lighting observation and command contract rather than guessed UI state.

This first slice therefore makes the page truthful immediately:

```text
Runtime environmental observation
  -> body-state snapshot
  -> Lighting context projection
  -> Founder Lighting room
```

Later lighting observers can extend the evidence side without teaching Interface to own hardware.

## Failure behavior

Missing, malformed, stale, degraded, failed, or authority-bearing environmental evidence is not replaced with synthetic healthy values. Stale evidence is marked stale and invalid evidence fails closed to unavailable.

The widget is mouse-transparent and does not interfere with the room's Home or Emergency image-surface press points.
