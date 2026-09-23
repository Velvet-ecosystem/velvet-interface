# Founder surface reachability

Founder keeps old artwork and lineage without pretending every retained surface is part of the current navigation graph.

## Current rule

Every `navigate:<scene>` action in an image-surface manifest must resolve to either:

- another loaded Founder surface manifest; or
- a trusted built-in scene registered by application code.

The automated reachability test checks this contract so a renamed or removed surface cannot silently leave a dead touchpoint behind.

Trusted built-in scenes currently include:

```text
written_conversation
character_foundry
eleanor_engineering
surface_studio
library_reader
owner_maintenance
```

Some built-ins may be disabled or unavailable at launch. Their own access/provider boundaries remain responsible for failing closed.

## Retained but intentionally unrouted surfaces

The following image surfaces remain in the repository for lineage, artwork recovery, and deliberate future work, but no current Founder manifest should target them:

```text
listen
silent
private
forge_workspace
```

Their roles are different:

- `listen` preserves older dedicated-listening artwork. Current listening evidence is handled by Home/Written Conversation/Audio/Backroom paths.
- `silent` preserves older silent-mode artwork. A real mute or silent-listening control still requires a reviewed Runtime/audio intent path; a decorative page must not pretend to mute microphones.
- `private` preserves the owner-private/boudoir visual lineage. It is explicitly separate from Backroom and the protected owner-maintenance hierarchy. It remains deferred until its owner/private access and safe-state rules are implemented deliberately.
- `forge_workspace` was the generic Scroll landing page used before Engineering Design, Module Lab, and Test Bench received dedicated workspaces. It remains only as a compatibility/lineage fallback.

Retained does not mean active. Deferred surfaces should not become accidental Front Room routes merely because their image files still exist.

## Backroom versus protected owner maintenance

The Front Room has a discreet Backroom seam. Backroom is the technical/read-only diagnostics room.

The deeper protected owner-maintenance entrance is different: its Backroom press point emits a local presentation event and application code requires both owner-presence and protected-maintenance evidence before opening the trusted built-in scene. No manifest directly navigates to `owner_maintenance`.

This keeps the visible room reachable while preserving the hidden owner-maintenance boundary.

## Physical mapping

Reachability and access contracts are independent of final touch geometry. Provisional Backroom and hidden-maintenance targets may be moved during Founder placement-debug work without changing their semantic route or authority posture.
