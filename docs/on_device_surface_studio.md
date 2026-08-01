# On-device Surface Studio

Surface Studio is Velvet's maintenance-only interface workshop. It lets Mister
create or change full-screen artwork, press points, and registered widget
placements directly on the Founder OS without editing YAML by hand.

It is a trusted built-in scene named `surface_studio`. Surface manifests may
navigate to it, but they cannot provide or replace its code.

## Maintenance entrance

Add a protected press point to the Maintenance surface:

```yaml
press_points:
  - id: open_surface_studio
    coordinate_space: normalized
    polygon:
      - [0.82, 0.84]
      - [0.98, 0.84]
      - [0.98, 0.98]
      - [0.82, 0.98]
    action: navigate:surface_studio
    accessibility_label: Open Surface Studio
```

The actual polygon belongs on the chosen Maintenance artwork. The coordinates
above are an example only and should be replaced in placement-debug mode.

When Maintenance is already unlocked, `Ctrl+Alt+S` is also available as a
service shortcut. The shortcut does nothing while Maintenance is locked.

## What can be done on-device

Surface Studio can:

- import a PNG or JPEG into its private managed asset directory;
- capture the current real still published by a trusted camera feed;
- create a blank PNG background at a chosen resolution and colour;
- paint simple translucent panels and text directly into the draft artwork;
- draw polygon press points over the artwork;
- bind press points only to `navigate:<scene>` or `emit:<event>` actions;
- place explicitly registered widget IDs by drawing rectangles;
- open and revise saved drafts;
- hide or show placement guides;
- preview the actual background, crop mode, presses, and widget geometry;
- validate and save normalized surface YAML;
- promote a validated draft and hot-reload the active scene without restarting
  the full interface.

It is intentionally not a general shell, Python editor, plugin loader, Runtime
console, CAN tool, actuator editor, or full photo editor.

## Camera-frame capture

Surface Studio does not open camera devices directly. A camera organ owns the
stream and atomically publishes one current still. Founder defaults to:

```text
/run/velvet/camera/latest-frame.jpg
```

The path, source identity, and freshness window can be configured with:

```bash
export VELVET_CAMERA_FRAME_PATH=/run/velvet/camera/latest-frame.jpg
export VELVET_CAMERA_SOURCE_ID=camera.front
export VELVET_CAMERA_FRAME_MAX_AGE=3.0
```

The camera publisher should write a temporary file in the same directory and
then replace the latest-frame path atomically. The Surface Studio capture button
reads the file only at the moment Mister presses it.

A capture is rejected when the current-frame file is:

- missing;
- a symbolic link;
- older than the configured freshness window;
- untrustworthily timestamped in the future;
- larger than the Surface Studio asset limit;
- not PNG or JPEG;
- malformed or changed while it is being read;
- undecodable by Qt.

There is no placeholder or simulated fallback. A rejected capture leaves the
existing draft untouched.

A successful capture:

1. receives a capture receipt ID;
2. is copied into the private managed asset directory;
3. appends `receipts/camera-captures.jsonl`;
4. creates a new draft with camera-source provenance in its metadata;
5. enters the normal press-point, widget, validation, and promotion path.

Capturing a frame grants no camera control, Runtime authority, route, executor,
or actuation.

## Draft and active separation

The default development workspace is:

```text
.velvet-dev/surface-studio/
  assets/
  drafts/
  backups/
  receipts/camera-captures.jsonl
  receipts/surface-promotions.jsonl
```

A deployed Founder can set:

```bash
export VELVET_SURFACE_STUDIO_WORKSPACE=/var/lib/velvet-interface/surface-studio
```

Draft editing is isolated inside that workspace. A draft cannot silently become
an active interface.

Promotion requires all four pieces of evidence at the moment the Promote button
is pressed:

```bash
export VELVET_MAINTENANCE_UNLOCKED=1
export VELVET_OWNER_PRESENT=1
export VELVET_VEHICLE_STATIONARY=1
export VELVET_PHYSICAL_CONTROL_DISABLED=1
```

These environment inputs are a fail-closed Founder integration seam, not the
final Court implementation. Later Runtime/Court work should replace them with a
local presence grant and a receipted maintenance capability. Missing or false
evidence blocks promotion.

Every successful promotion:

1. validates the draft and its real artwork;
2. copies the artwork into the active surface asset directory;
3. backs up the prior active manifest and artwork when present;
4. writes the new active manifest atomically;
5. appends a promotion receipt;
6. invalidates the old Qt scene widget;
7. registers and displays the newly promoted surface.

Promotion changes presentation only. It grants no authority, execution, route,
executor, hardware target, CAN transmission, or physical actuation.

## Launching Founder with Surface Studio

```bash
python examples/founder_surface_window.py \
  --surfaces /var/lib/velvet-interface/surfaces \
  --surface-workspace /var/lib/velvet-interface/surface-studio \
  --camera-frame-path /run/velvet/camera/latest-frame.jpg \
  --camera-source-id camera.front \
  --camera-frame-max-age 3.0 \
  --initial home \
  --width 1280 \
  --height 720 \
  --fullscreen
```

Use `--disable-surface-studio` for a locked demonstration image that must not
expose the editor at all.

## Recommended operating doctrine

Surface Studio belongs behind Velvet's hidden Maintenance entrance, historically
represented by the candle/Legs path. Opening the studio may be allowed while
stationary for draft work. Promoting an active surface should remain owner-only,
stationary-only, physical-control-disabled, and receipted.

A surface can be beautiful, strange, theatrical, or newly forged at midnight.
Its geometry still does not become authority.
