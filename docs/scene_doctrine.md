# Scene Doctrine

This repo implements Velvet's scene-based interface model.

The canonical doctrine lives in:

- `velvet-ai-core/docs/scene_doctrine.md`

In this repo, scenes are treated as interface surfaces only. They may display controls, route intent, reveal overlays, and adapt to context, but they must never directly execute hardware actions.

Correct flow:

    Scene object
      -> intent event
      -> identity/context check
      -> policy authorization
      -> capability token check
      -> safety gate
      -> executor
      -> receipt

Forbidden flow:

    Scene object
      -> relay / CAN / actuator

Interface scenes may be expressive, hidden, passenger-aware, and body-aware, but authority remains outside the scene layer.