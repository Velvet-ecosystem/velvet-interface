# Character Foundry workspace UI

The Character Foundry is a trusted full-screen Interface scene backed by Persona Continuity's canonical `FoundryService` through `FoundryBridge`.

## Visual composition

The working surface reuses `examples/assets/workspace_scroll.png`. This is intentional: the scroll is a reusable Interface workspace rather than a room-specific control panel.

The initial PyQt composition is three-part:

1. **Draft Library** — local candidate list, kind selection, scaffold/open/discard actions.
2. **Candidate Draft** — structured identity, purpose, character/role, evidence, and advanced canonical JSON views.
3. **Foundry Guardrails / Promotion Review** — immutable authority-free posture plus the external-review-required promotion plan.

The UI may edit candidate intent. It does not decide candidate validity, authority, capability, lineage, merge, deployment, or actuation.

## Forge placement

`examples/surfaces/forge.surface.yaml` introduces the Forge room using `../assets/forge.png`.

The Forge is broader than Character Foundry. It is the builder workspace for character, software-module, hardware-module, testing, and future Interface creation tools.

The Forge manifest intentionally contains only the already-standard Return Home and Emergency press points. The Character Foundry entry point must be mapped from the actual artwork using placement-debug rather than guessed coordinates.

Expected final flow:

`Founder Home -> Forge room -> mapped physical workspace object -> Character Foundry -> reusable workspace_scroll.png editor`

## Access

Character Foundry access must fail closed. The live launcher should register the scene only with a trusted local `FoundryBridge` and an access provider representing verified owner presence or protected maintenance access.

Access to the scene never grants Foundry promotion authority.

## Persistence and conflicts

All create, inspect, update, discard, validate, and promotion-plan operations cross `FoundryBridge` into the canonical Persona service.

Persisted updates and discard operations use the canonical content hash returned by Persona Continuity. A stale edit is rejected by the service rather than silently overwriting another surface's work.

## Promotion

The promotion rail displays the canonical plan. `promotion_decision` remains `external_review_required`; handoffs remain non-automatic and authority-free.

The Interface does not add buttons that directly:

- insert Identity Registry records,
- certify Riven lineage,
- grant Runtime/Court capability,
- mint Court tokens,
- merge repositories,
- deploy software,
- actuate hardware.

Those are external governed responsibilities, not Interface controls.

## Launcher wiring

This stacked UI change does not modify the live Founder launcher while the underlying Interface boundary PR remains unmerged. After the boundary lands on `main`, the UI branch should be retargeted, refreshed against resulting `main`, and launcher registration added as the final bounded step before the Character Foundry scene becomes reachable in normal operation.
