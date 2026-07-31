# Image Surface Layouts

Velvet's full interface screens are image-first surfaces. Each surface is one background artwork plus normalized press points and explicitly registered widget anchors.

The layout file is presentation data. It cannot dynamically import code, call a shell, select an executor, carry a capability token, or grant physical authority.

## Surface package

A practical surface set looks like this:

```text
velvet-interface/
  surfaces/
    home.surface.yaml
    drive.surface.yaml
    forge.surface.yaml
    house.surface.yaml
    industrial.surface.yaml
  assets/
    home.png
    drive.png
    forge.png
    house.png
    industrial.png
```

Paths in a manifest are resolved relative to that manifest. Production loading can require the background to exist. Missing images stay visibly unavailable and are never replaced with synthetic artwork.

## Manifest contract

```yaml
schema: velvet.interface.surface.v1
name: home
base_resolution: [1920, 1080]
background:
  image: ../assets/home.png
  fit: cover
  alt_text: Velvet home surface

press_points:
  - id: drive_space
    coordinate_space: normalized
    polygon:
      - [0.05, 0.70]
      - [0.24, 0.70]
      - [0.24, 0.92]
      - [0.05, 0.92]
    action: navigate:drive
    accessibility_label: Open Drive
    enabled: true

widgets:
  - widget_id: founder_body_status
    coordinate_space: normalized
    rect: [0.72, 0.05, 0.24, 0.19]
    visible_in: [owner, service]
```

Normalized coordinates remain attached to the artwork when Founder runs at a different resolution. The same transform controls background placement, press-point hit testing, widget geometry, and authoring overlays.

Supported background fits:

- `stretch`: independently fills width and height
- `contain`: shows the complete image with letterboxing
- `cover`: fills the display and crops symmetrically

Supported press actions are deliberately narrow:

- `navigate:<scene>` changes Interface scenes through the Router
- `emit:<event>` emits a presentation event to a registered scene handler

Control requests will use a separate reviewed Interface-to-Runtime request contract. A press point is not actuator authority.

## Visual authoring

Create a new surface directly on its real image:

```bash
python examples/surface_layout_editor.py \
  --manifest surfaces/home.surface.yaml \
  --image assets/home.png \
  --name home \
  --surface-size 1280x720
```

Editor controls:

- left-click adds polygon vertices
- Enter names and commits the press point
- right-drag creates a widget rectangle
- Ctrl+S writes the YAML manifest
- Escape clears the unfinished polygon

The editor prints normalized coordinates as each point is selected. Existing manifests can be reopened and extended.

## Full Founder launcher

After placing the real backgrounds:

```bash
python examples/founder_surface_window.py \
  --surfaces surfaces \
  --initial home \
  --width 1280 \
  --height 720 \
  --placement-debug
```

The launcher:

1. requires real background assets;
2. loads all valid surface manifests;
3. registers each `ImageScene` with the normal Router;
4. places only widget IDs supplied by trusted application code;
5. refreshes `founder_body_status` from the bounded boot and body snapshot files;
6. leaves unknown widget IDs absent;
7. leaves physical control exactly as reported by the verified boot snapshot.

`--placement-debug` draws red press polygons and blue widget anchors above the image. Every click also prints its normalized position.

## Moving beyond the proof window

The existing Founder proof window remains useful for boot troubleshooting. The full launcher is the replacement path for normal operation:

```text
verified boot and body snapshots
  -> registered read-only widgets
  -> image surface manifest
  -> QtSurface
  -> Router
  -> Home / Drive / Forge / House / Industrial screens
```

The background image supplies the room. Press points supply navigation. Widgets supply live evidence. Runtime, Court, safety gates, executors, and Receipts remain outside the artwork and keep their existing authority boundaries.
