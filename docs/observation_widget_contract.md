# Observation Widget Contract

Velvet Interface renders sanitized observations supplied by Velvet Runtime or the event protocol.

It does not decode raw CAN frames, load vehicle profiles, select executors, choose capabilities or hardware targets, create control commands, or actuate hardware.

`ObservationWidget` accepts only bounded scalar values with:

```text
name or signal_name
value
confidence
observed_at or timestamp
source_profile
status: observation-only
read_only: true
actuation_granted: false
actuation_performed: false
```

An optional `unit` may be displayed.

The widget rejects executor, route, capability, token, command, shell, target, hardware, and actuation fields.

Presentation state is derived locally:

- confidence at or above `0.8` is shown as `validated`
- lower confidence is shown as `provisional`
- age beyond the stale threshold is shown as `stale`
- freshness is `unknown` when no current clock value is supplied

These labels are presentation hints only. They do not grant authority or qualify a signal for vehicle control.

Canonical flow:

```text
Runtime can-signals output
  or DECODED_CAN_SIGNAL_OBSERVED event
    -> ObservationWidget.update_observations()
    -> surface-specific render()
```
