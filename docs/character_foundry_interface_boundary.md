# Character Foundry Interface Boundary

Status: Interface integration foundation. The live Founder launcher is intentionally unchanged by this change.

## Purpose

Character Foundry is a substantial protected tool, not a small manifest widget. Interface therefore hosts it as a trusted built-in scene, following the same architectural family as Surface Studio and Written Conversation.

The canonical Foundry implementation remains in `velvet-persona-continuity`. Interface owns presentation, access gating, and navigation only.

## Canonical service boundary

`velvet_interface.foundry_bridge.FoundryBridge` lazily loads `velvet_persona.foundry_service.FoundryService` when Persona Continuity is installed.

The bridge:

- does not implement fallback candidate semantics;
- does not reinterpret validation results;
- does not grant authority or capabilities;
- does not insert Identity Registry records;
- does not certify Riven lineage;
- does not execute Runtime/Court capability review;
- does not merge or deploy candidates;
- converts canonical service results into plain presentation data only.

If Persona Continuity is absent, the Foundry is unavailable rather than silently reimplemented inside Interface.

## Trusted scene

`CharacterFoundryScene` is application-registered code, never a dynamically imported surface-manifest component.

The scene is intended for verified owner presence or protected maintenance access. Access-provider failure is fail-closed.

The current scene is deliberately a readiness shell. It is not registered in the live Founder launcher until the structured editor exists, so production surfaces do not expose a dead-end tool.

## Planned editor operations

The future editor must call the bridge for the canonical operations already supplied by Persona Continuity:

- scaffold candidate;
- validate candidate;
- create draft;
- inspect draft;
- list drafts;
- conflict-protected update;
- confirmed discard;
- propose promotion.

The editor must preserve canonical optimistic content hashes. It may present promotion handoffs but may not execute or reinterpret them.

## Placement

Permanent placement is intentionally separate from this integration boundary.

Current recommendation: a future **Forge** image surface should contain the physical-looking entry point to Character Foundry. This fits the Interface doctrine that Forge is the builder workspace for tools, modules, testing, and creation and avoids coupling Foundry to Vehicle, Archive, or another single domain.

The current `backroom` surface is explicitly temporary and should not be canonized as the permanent Foundry location merely because it is available.

No existing surface manifest or press point is changed here.

## Next review unit

The next Interface PR should atomically add:

1. the structured PyQt Character Foundry editor;
2. trusted launcher registration;
3. owner/maintenance access wiring;
4. tests for editor-to-bridge parity and stale-edit handling.

A separate visual/placement change may then add the Forge artwork and its `navigate:character_foundry` press point once the desired room image and entry object are chosen.
