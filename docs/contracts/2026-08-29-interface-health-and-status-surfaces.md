# Interface health and status surface contracts

Date: 2026-08-29
Status: contract draft
Owner repo: velvet-interface

## Purpose

Interface should display body truth without becoming the authority boundary. These contracts describe how future surfaces can show camera quality, node health, low-power status, evidence triggers, and last-known-safe state.

## 1. Interface Authority Rule

The interface may show status, request action, and display refusal reasons. It must not create authority.

Rules:

- UI approval is not a security boundary.
- Court and Runtime decide whether capability dispatch is allowed.
- Displayed availability must come from live capability registry or receipted state.
- A stale screen cannot authorize physical action.

## 2. Camera Quality Health Surface

A live stream is not proof that useful vision survived.

Displayable fields:

```yaml
camera_id: string
online: boolean
camera_quality_state: good | degraded | failed | unknown
center_detail_confidence: number | null
edge_detail_confidence: number | null
low_light_confidence: number | null
nir_confidence: number | null
motion_blur_warning: boolean
dropped_frame_rate: number | null
exposure_stability: good | degraded | failed | unknown
distortion_calibration_age_hours: number | null
minimum_pixels_on_critical_feature_ok: boolean | null
last_quality_check: string | null
```

Use cases:

- driver monitoring
- occupant monitoring
- medical observation
- perimeter awareness
- garage/workshop cameras

## 3. Low-Power Status Surface Concept

Future removable status surfaces may survive crashes, sleep, and power cuts better than a live UI.

Useful display roles:

- node health card
- current fault card
- wiring or harness identification
- bench-test steps
- last receipt ID
- recovery code
- power state
- current module lifecycle state
- offline maintenance note
- last known safe status

Preferred traits:

- persistent display such as e-paper
- local-only operation
- low-power update mode
- timestamped last refresh
- NFC or QR commissioning helper optional
- safe if disconnected

## 4. Refusal Reason Display

When Velvet refuses an action, the UI should show a safe reason without exposing sensitive internals.

Allowed public-style reasons:

```text
capability unavailable
capability degraded
authority missing
owner presence required
vehicle state disallows action
maintenance mode required
sensor data stale
manual override required
```

Sensitive details such as exact token names, private hardware IDs, or security bypass internals should remain in receipts/logs, not on public display.

## 5. Evidence Trigger Display

When event evidence capture starts, the interface may display:

```yaml
trigger_reason: string
capture_state: started | complete | partial | failed
privacy_class: public | internal | private | sensitive
receipt_id: string
user_action_needed: boolean
```

Rule: evidence capture display is informational. It does not imply the UI owns the stored data or the decision that triggered capture.

## 6. Last-Known-Safe State

For low-power, e-paper, or crash-persistent surfaces, always show:

```yaml
last_updated_at: string
source_node: string
state_age_ms: integer
state_is_stale: boolean
last_known_safe_state: string | null
recovery_hint: string | null
receipt_id: string | null
```

## 7. Health Trend Display

Velvet should show not only current health but direction:

```yaml
module_id: string
current_state: good | degraded | failed | unknown
trend_direction: improving | stable | worsening | unknown
recurring_offender: boolean
last_fault_summary: string | null
receipt_id: string | null
```

## Non-goals

- No UI-created authority.
- No hidden command surface.
- No baked-in secrets, physical identities, or owner-specific sensitive state in public UI assets.
