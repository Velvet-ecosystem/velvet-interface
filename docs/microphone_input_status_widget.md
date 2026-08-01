# Microphone Input Status Widget

Surface Studio may place the registered widget:

```text
microphone_input_status
```

The widget reads only the Runtime body-state snapshot. It does not open ALSA devices, capture audio, retain PCM, perform speech recognition, detect wake words, identify speakers, or interpret commands.

It displays:

- Runtime health state;
- configured ALSA device alias;
- channel count and sample rate;
- active and quiet channel counts;
- freshness;
- each configured physical channel label and its latest signal state.

Supported channel states are:

```text
ACTIVE
QUIET
DIGITAL_SILENCE
CLIPPING
```

Quiet is presented as healthy. Exact digital silence and clipping remain visible as degraded evidence. A stale packet remains visible as the last genuine observation but is labeled `STALE`.

A failed source does not fabricate channel count, levels, or activity. The card reports `FAILED` with no invented microphone evidence.

The projection also fails closed unless Runtime explicitly states that audio was not retained, persisted, recognized, wake-word processed, command interpreted, or granted voice-command authority.

Example Surface Studio placement:

```yaml
widgets:
  - id: microphone_input_status
    rect: [0.04, 0.56, 0.36, 0.38]
```

The rectangle is an example only. Adjust it for the selected artwork and screen geometry.
