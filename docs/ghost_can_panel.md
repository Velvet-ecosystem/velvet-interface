# Ghost CAN Panel

The Ghost CAN panel is the public interface view for Velvet's jarred vehicle demo. It displays `vehicle.can.ghost_observation` events produced by the public Runtime and CAN repos, but it never opens a physical bus, selects an executor, sends CAN frames, or grants vehicle authority.

The panel verifies these public safety claims before rendering:

- `read_only: true`
- `synthetic_fixture: true`
- `physical_bus_opened: false`
- `hardware_bus_opened: false`
- `can_transmission_attempted: false`
- `can_transmission_performed: false`
- `actuation_granted: false`
- `actuation_performed: false`
- `authority_granted: false`

Authority-shaped fields such as `command`, `executor`, `route_id`, `target`, `hardware_target`, `shell`, or `token` produce a blocked view model.

## Demo

```bash
python examples/ghost_can_panel.py
```

This module is glass, not fingers. It may show runtime observations and receipts. It must not decode raw CAN, request routes, open hardware, or claim physical control.
