# Scene Interface Contract

This repo implements Velvet's scene-based interface model.

The canonical doctrine lives in:

- `velvet-ai-core/docs/scene_doctrine.md`
- `velvet-ai-core/docs/room_body_interface.md`

This document defines the interface repo's local contract.

In this repo, scenes are treated as interface surfaces only. They may display controls, route intent, reveal overlays, adapt to context, and represent body state, but they must never directly execute hardware actions.

Correct flow:

    Scene object
      -> intent event
      -> identity / context check
      -> policy authorization
      -> capability token check
      -> safety gate
      -> executor
      -> receipt

Forbidden flow:

    Scene object
      -> relay / CAN / actuator

Interface scenes may be expressive, hidden, passenger-aware, profile-aware, and body-aware.

Authority remains outside the scene layer.

## Interface Responsibilities

The interface layer may:

- render scenes
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
- treat hidden access as permission
- treat passenger presence as authority
- treat a wake phrase as authorization
- silently ignore degraded body state
- assume organs exist without registry confirmation

## Public Rule

Scenes express.

Policies authorize.

Gates enforce.

Executors act.

Receipts remember.