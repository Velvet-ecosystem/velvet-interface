# Live Body-State Interface

Velvet Interface consumes trusted body observations and presents them without
becoming a hardware, policy, or authority layer.

## Input contracts

The body-state projection accepts the standard Event Protocol records produced
by:

- `SensorPacket.to_event_protocol()`
- `HealthEvent.to_event_protocol()`

The Interface package does not import AI Core at runtime. It validates the
stable transport shape so the display remains loosely coupled to the producer.

## Flow

```text
physical or simulated adapter
  -> SensorPacket / HealthEvent
  -> Event Protocol
  -> Runtime transport or local read-only bridge
  -> BodyStateStore
  -> BodyStateSnapshot
  -> DiagnosticsScene and future body-aware scenes
```

The same projection is used for real and simulated observations. Simulation
must remain labelled by the producer and cannot unlock physical controls.

## Latest-value behavior

`BodyStateStore` retains the newest sensor and health record for each
`module_id`. A snapshot includes:

- current sensor observations
- current health transitions
- freshness calculated from monotonic time
- receipt identifiers
- a bounded presence recommendation
- explicit read-only and no-actuation claims

The presence recommendation is presentation only:

- no evidence: `idle`
- normal evidence: `observing`
- degraded or stale evidence: `warning`
- recovering evidence: `recovery`
- failed or critical evidence: `critical`

It does not alter Runtime state or grant authority.

## Diagnostics behavior

`DiagnosticsScene` now accepts an optional body-state provider. The provider may
return a `BodyStateSnapshot` or a validated mapping.

Without a provider, the scene says it is waiting for Runtime body state. It no
longer invents module counts, memory usage, or uptime.

Provider failure is displayed honestly as `STATE UNAVAILABLE`. The scene keeps
physical control disabled and does not silently substitute synthetic normal
status.

## Authority boundary

Body-state input is rejected when it contains authority-bearing fields such as:

- capability or capability token
- executor or executor name
- command or action
- route identifier
- hardware target
- shell or token

The rejection is recursive, including nested sensor and diagnostic payloads.
This prevents a display record from becoming a concealed request channel.

```text
Interface observes and requests.
Runtime verifies and coordinates.
Court authorizes.
Executors act.
Receipts remember.
```

## Next integration step

Runtime should provide a bounded local stream or snapshot provider containing
only SensorPacket and HealthEvent records already accepted by its event and
receipt paths. Founder Qt can then refresh `DiagnosticsScene` from live UP2 body
data without adding hardware logic to the rendering layer.
