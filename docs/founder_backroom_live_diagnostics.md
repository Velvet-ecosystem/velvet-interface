# Founder Backroom live diagnostics

The Backroom is a read-only technical surface for current Founder evidence. It uses existing trusted widgets rather than creating a second diagnostics stack.

Current Backroom cards:

```text
founder_body_status
vehicle_power_status
gnss_status
microphone_input_status
seat_presence_status
nfc_status
```

Each card consumes the same bounded evidence source it already uses elsewhere in Founder. The Backroom does not acquire hardware handles, duplicate Runtime logic, or synthesize healthy values when evidence is missing.

## Authority boundary

The Backroom remains:

```text
posture: presentation-only
physical_control: disabled
```

Its only press-point actions are navigation to Home and Emergency. It exposes no restart, update, maintenance unlock, Court grant, shell command, relay, CAN, or actuator action in this slice.

This is intentional. The official Backroom design eventually calls for safe restart/update and deeper diagnostics, but those actions must arrive through reviewed authority-bearing contracts rather than by teaching an image surface to execute them directly.

## Placement

The six cards are arranged as a diagnostic wall in two rows. Their placement is suitable for software review and may be tuned during the next physical Founder layout pass without changing the evidence contracts.

## Contactless status

The Backroom includes `nfc_status` because contactless verification is useful diagnostic evidence. The reader itself remains headless Runtime infrastructure and does not depend on this card being visible.
