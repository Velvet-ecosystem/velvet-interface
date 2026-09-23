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

## Front Room entry

The Front Room again preserves the historical discreet Backroom seam. The current software geometry is a provisional narrow right-edge target and is deliberately marked `provisional-until-founder-mapping` so the next physical Founder pass can bind it to the actual seam/keyhole detail in the artwork.

The Front Room entry navigates only to the read-only Backroom surface. It does not enter the deeper owner-maintenance room and grants no new authority. Backroom evidence cards remain visible only in their existing owner/service presentation modes, so a guest presentation does not gain technical evidence merely by reaching the room.

## Velvet's Legs hidden maintenance layer

Backroom also preserves the historical owner-only maintenance path known as **Velvet's Legs**.

The visible Backroom remains the diagnostic room. The deeper route is intentionally concealed in the artwork and uses an `emit:` press point rather than direct navigation. Founder application code decides whether that event may open the built-in `velvets_legs` scene.

The current development presentation seam requires both:

```text
VELVET_OWNER_PRESENT=true
VELVET_MAINTENANCE_UNLOCKED=true
```

One without the other is insufficient. When either input is absent or false, pressing the concealed region does nothing and the Backroom remains visually ordinary. Direct navigation to the built-in scene also fails closed to a locked presentation.

These environment values are temporary Founder integration evidence. They do not create identity, Court authority, execution authority, or physical control. The final path should consume the reviewed owner/presence and maintenance-capability contracts when those replace the development seam.

Surface Studio is the first live tool exposed inside Velvet's Legs. It retains its own maintenance gate and promotion requirements. Learning Mode, White Room, Dream Layer, and deeper owner maintenance tools remain separate reviewed work rather than placeholders pretending to be operational.

The current concealed polygon is provisional and must be mapped against the real Founder Backroom artwork during the next physical placement pass. Moving that target does not change the access contract.

## Authority boundary

The Backroom remains:

```text
posture: presentation-only
physical_control: disabled
```

Its ordinary visible press points navigate only to Home and Emergency. The concealed owner-maintenance point emits a local presentation event and cannot itself navigate, unlock maintenance, grant Court authority, invoke shell commands, drive relays, transmit CAN, or actuate hardware.

Velvet's Legs is also presentation-only in this slice. Opening the hidden room does not expand execution scope. If `VELVET_PHYSICAL_CONTROL_DISABLED` is not positively present, the room reports that disabled posture as unproven rather than inferring safety.

This is intentional. The official Backroom design eventually calls for safe restart/update and deeper diagnostics, but those actions must arrive through reviewed authority-bearing contracts rather than by teaching an image surface to execute them directly.

## Placement

The six cards are arranged as a diagnostic wall in two rows. Their placement is suitable for software review and may be tuned during the next physical Founder layout pass without changing the evidence contracts.

The Front Room Backroom seam and the concealed Backroom-to-Legs entrance are both provisional geometry. Board-time placement should move either target to the correct artwork feature without changing the routing or access contracts.

## Contactless status

The Backroom includes `nfc_status` because contactless verification is useful diagnostic evidence. The reader itself remains headless Runtime infrastructure and does not depend on this card being visible.
