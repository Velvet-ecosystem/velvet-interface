# Scene Interface Contract

This repo implements Velvet's scene-based interface model.

The canonical doctrine lives in:

- `velvet-ai-core/docs/scene_doctrine.md`
- `velvet-ai-core/docs/room_body_interface.md`

This document defines the interface repo's local contract.

In this repo, scenes are treated as interface surfaces only. They may display controls, route intent, reveal overlays, adapt to context, and represent body state, but they must never directly execute hardware actions.

A scene does not have to be permanently visible. Velvet may operate voice-first with no visual layer, use a minimal glow or orb when presence should be shown, or reveal a full surface when the task requires visual control.

Visible surfaces may use a user-selected image with mapped polygon or press-point regions. Those regions route intent. They do not grant authority and they do not directly actuate hardware.

Correct flow:

    Voice / scene object / press point / widget
      -> intent event
      -> identity / context check
      -> policy authorization
      -> capability token check
      -> safety gate
      -> executor
      -> receipt

Forbidden flow:

    Scene object / press point / presence indicator
      -> relay / CAN / actuator

Interface scenes may be expressive, hidden, passenger-aware, profile-aware, and body-aware.

Authority remains outside the scene layer.

## Ambient-First Rule

Velvet is not a screen. Screens are temporary bodies used when speech alone is insufficient.

The default interface may be invisible and voice-first. Visual escalation should reveal only as much interface as the task requires:

1. voice only
2. minimal presence indicator
3. temporary status or choice card
4. focused control or receipt panel
5. full visual surface

The interface should return toward the lowest useful level after the interaction.

Surface transitions may change the image, mapped regions, controls, and local body state while preserving Velvet's identity and conversational continuity.

The surface may change completely. Velvet does not.

See also:

- [Ambient Presence Doctrine](ambient_presence_doctrine.md)

## Interface Responsibilities

The interface layer may:

- render scenes
- remain visually absent while voice interaction is available
- display an optional presence state such as a glow, orb, pulse, mark, waveform, or avatar
- load user-selected surface images
- bind mapped interaction regions to intent events
- transition smoothly between surfaces
- preserve conversational continuity across transitions
- display body state
- expose authorized controls
- route user intent into events
- request confirmation
- show degraded state
- hide or reveal surfaces based on context
- present startup identity state

The interface layer may not:

- bypass authorization
- directly actuate hardware
- treat a concealed control as permission
- treat passenger presence as authority
- treat a wake phrase as authorization
- silently ignore degraded body state
- assume organs exist without registry confirmation
- preserve stale permissions across a surface transition

## Public Rule

Scenes express.

Presence communicates.

Press points route intent.

Policies authorize.

Gates enforce.

Executors act.

Receipts remember.
