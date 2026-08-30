# Runtime Surface Sets

Velvet Interface already owns the image-first surface renderer, strict surface manifests, press points, widget placement, scene router, and transitions. A body should not fork that machinery merely to choose different artwork.

A runtime surface set is the small presentation binding that selects:

- the directory containing approved `velvet.interface.surface.v1` manifests
- the preferred initial scene

It does not select Runtime, Court, executors, capabilities, hardware drivers, credentials, or physical authority.

## Binding contract

```yaml
schema: velvet.interface.surface-set.v1
name: velvet_home
surface_directory: scenes
initial_scene: home_front_room
```

`surface_directory` is resolved relative to the binding file when it is not absolute. Each surface manifest then resolves its own background image relative to that manifest. This keeps a body package portable between machines and installation roots.

## Launcher selection

The Founder launcher accepts:

```bash
python3 -m velvet_interface.founder_surface_launcher \
  --surface-set /path/to/body/surfaces/home.surface-set.yaml
```

or:

```bash
export VELVET_SURFACE_SET_PATH=/path/to/body/surfaces/home.surface-set.yaml
python3 -m velvet_interface.founder_surface_launcher
```

Development overrides remain available:

- `--surfaces` overrides the bound surface directory
- `--initial` overrides the bound initial scene

Without a surface-set binding, the launcher preserves the existing Founder defaults: `examples/surfaces` and `founder_home`.

## Body ownership

The body repository owns body-specific surface content and its surface-set binding. Velvet Interface owns rendering and routing.

For example:

```text
Velvet_home/
  surfaces/
    home.surface-set.yaml
    scenes/
      home_front_room.surface.yaml
      home_climate.surface.yaml
      assets/
        home_front_room.png
        home_climate.png
```

The same interface package can therefore render a vehicle, Home node, cyberdeck, workshop, or later body by changing presentation content rather than changing interface architecture.

## Failure posture

A malformed or missing surface-set binding fails before the Qt window starts. A missing requested initial scene does not invent content; the existing launcher chooses another valid registered surface or Surface Studio when available.

Surface-set files reject authority-bearing and secret-bearing fields. Presentation selection is not permission to act.
