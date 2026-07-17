# Velvet Interface Framework

**Scene-based, image-first, multi-surface presentation framework for the Velvet ecosystem.**

Velvet Interface is where people meet Velvet. It renders living spaces, contextual controls, body state, organ presence, receipts, and requests across embedded Qt, desktop, mobile, web, and future custom surfaces.

It is presentation and interaction, not physical authority.

> Scenes express. Interface requests. Runtime verifies and coordinates. Court authorizes. Executors act. Receipts remember.

## Current Status

Velvet Interface is an alpha-stage framework with:

- surface-agnostic scenes
- Qt rendering support
- YAML image-scene definitions
- polygon interaction regions
- automatic scaling
- scene routing and lifecycle
- transitions and reusable widgets
- desktop, automotive, mobile, industrial, and robotics examples
- a public scene interface contract
- image-first interaction suitable for an ambient vehicle display

Current physical authority in Interface: **none**.

Interface does not directly control CAN, relays, locks, lighting, climate hardware, seats, steering, throttle, brakes, files, shell commands, or other actuators.

## House, Not Dashboard

Velvet is not designed as a permanent grid of buttons and gauges.

The interface uses a **room-body model**: each scene is a place with a purpose, atmosphere, organ relationship, and bounded interaction vocabulary.

A scene should answer:

- Where am I?
- Which part of Velvet is present here?
- What body state is being expressed?
- Which requests are appropriate here?
- What evidence supports the displayed state?

Scenes are not decorative menu backgrounds. They are spatial expressions of context.

## Living Spaces

Current and planned spaces include:

- **Home**: Velvet's ambient owner-facing presence and primary resting space
- **Drive**: Charlotte's driving, route, and vehicle-motion space
- **Cabin**: Jade's comfort, climate, air-quality, seat, and lighting space
- **Diagnostics / Garage**: Ruby's engine, ECU, maintenance, and observation space
- **Emergency / Medical**: Temperance's controlled crisis and guardian space
- **Library / Continuity**: Velour's receipts, history, archive, and lineage space
- **Security**: Sarah's trust, perimeter, access, and security-observation space
- **Forge**: the builder's workspace for tools, modules, testing, and creation
- **House / Industrial**: body-specific spaces for home, workshop, machinery, and future deployments

Named spaces do not grant named organs authority. They express responsibility and context inside the same Unified-Organ body.

## Presence Model

When Velvet is not being actively used, the interface should become quieter and more image-like, not behave like an attention-hungry dashboard.

Presence may be expressed through imagery, subtle motion, light, sound, text, widgets, or future displays.

Recommended presence states include:

- **sleeping**: display dark or deeply subdued; only required wake and safety paths remain visible
- **idle**: calm image-first scene with minimal persistent information
- **observing**: quietly aware of body and environment without interrupting
- **listening**: clear but restrained indication that voice input is active
- **thinking**: visible acknowledgement that a request is being interpreted
- **responding**: focused conversational or task presentation
- **working**: an approved operation is in progress and backed by Runtime state
- **warning**: important condition requiring attention without overstating emergency
- **critical**: unmistakable emergency presentation with protected controls and evidence
- **recovery**: degraded or failed state presented honestly, without pretending normal operation

Presence is not proof of authority. An animation saying "working" must be backed by trusted Runtime events or receipts.

## Image-First and Invisible Controls

Velvet's default visual state may be a cinematic or ambient image rather than a conventional control panel.

Controls should appear when context, touch, voice, proximity, mode, or safety state makes them useful. They should recede when no longer needed.

Image scenes may use:

- polygon touch regions
- contextual overlays
- protected interaction paths
- temporary controls
- subtle status marks
- receipt-backed detail panels
- voice-led navigation

Invisible does not mean undiscoverable. Critical controls, emergency actions, confirmation states, and accessibility paths must remain clear and testable.

## Human Modes

Presentation may adapt to verified Runtime context.

- **Owner mode** may expose the richest personal presentation and approved request vocabulary.
- **Guest mode** may use a more reserved personality and narrower visible controls.
- **Service mode** may prioritize diagnostics, maintenance evidence, and bounded technical requests.
- **Emergency mode** may temporarily replace normal scenes with a controlled safety surface.
- **Silent mode** may reduce voice and animation while preserving required alerts.

A visual mode does not create permission. Interface consumes verified identity, profile, session, body, and policy outcomes from Runtime.

## Authority Boundary

```text
human, voice, touch, or local client
  -> Interface scene
  -> route-approved request
  -> Runtime local intent gateway
  -> verified identity and body context
  -> authority hierarchy
  -> Court decision
  -> signed capability token
  -> execution contract
  -> resource coordination
  -> safety gate
  -> replay protection
  -> approved executor
  -> receipts
  -> Interface presentation
```

Clients may provide only the narrow fields allowed by the selected route, such as:

```text
intent_id
route_id
route-approved parameters
```

Interface must not let a scene, widget, plugin, image region, voice phrase, or remote client select raw capabilities, executor names, hardware targets, shell commands, module paths, Python callables, CAN writers, or actuator handles.

## Evidence-Backed Presentation

The interface should distinguish clearly between:

- requested
- authorized
- denied
- queued or waiting
- executing
- completed
- failed
- degraded
- observed only
- simulated or synthetic

Displayed state should come from trusted events, Runtime results, and receipts whenever available.

The interface must not convert an attractive animation into a false claim that hardware acted. Ghost Car and other synthetic demonstrations must remain visibly synthetic and non-authoritative.

## Pluggable Modules Above the Main System

Velvet is built so optional capabilities can be added above a stable main system.

```text
stable Interface core
  + scene contracts
  + surface adapters
  + bounded plugin modules
  = expandable Velvet presentation
```

New capabilities should arrive as scenes, widgets, adapters, and modules rather than forks of the core framework.

Examples may include:

- a greenhouse room
- a telescope surface
- a CNC or forge panel
- a boat helm
- a home-energy scene
- an accessibility package
- a vehicle-specific diagnostics room

Pluggable does not mean unrestricted. A module must declare its scene identity, required events, routes, assets, supported surfaces, lifecycle behavior, and authority boundary. It receives no hardware authority merely because it is installed.

A future dedicated Velvet Modules repository may provide reviewed optional modules and promotion records. Until that repository exists, this README treats it as planned architecture, not a current dependency.

## Scene and Module Rule

> New capabilities arrive as bounded modules and living spaces above the main system, not by cutting new authority holes through the foundation.

The stable layers remain:

- scene and surface contracts
- Runtime gateway boundary
- event and receipt interpretation
- accessibility and safety presentation laws

Optional modules may extend presentation and request vocabulary while remaining clients of those layers.

## Core Architecture

```text
┌─────────────────────────────────────────────┐
│ Human / Voice / Touch / Local Companion     │
└──────────────────────┬──────────────────────┘
                       ▼
┌─────────────────────────────────────────────┐
│ Velvet Interface                            │
│ scenes • presence • widgets • routing       │
│ images • overlays • accessibility           │
└──────────────────────┬──────────────────────┘
                       ▼
┌─────────────────────────────────────────────┐
│ Narrow Runtime Gateway                      │
│ route IDs • approved parameters             │
└──────────────────────┬──────────────────────┘
                       ▼
┌─────────────────────────────────────────────┐
│ Velvet Runtime                              │
│ Court • contracts • resources • safety      │
│ replay • executors • receipts                │
└──────────────────────┬──────────────────────┘
                       ▼
┌─────────────────────────────────────────────┐
│ Vehicle / Home / Forge / Industrial Body    │
└─────────────────────────────────────────────┘
```

## Core Concepts

### Scene

A logical living space with lifecycle, presentation, local UI state, and bounded request routes.

```python
class Scene(ABC):
    def on_enter(self, context) -> None: ...
    def on_exit(self) -> None: ...
    def render(self, surface) -> Any: ...
```

### Surface

A rendering backend such as Qt, web, mobile, or another body-specific display.

```python
class Surface(ABC):
    def show_scene(self, scene) -> Any: ...
    def show_text(self, text, x, y, ...) -> Any: ...
    def show_button(self, label, x, y, ...) -> Any: ...
```

### Router

Manages registered scenes, navigation history, and lifecycle transitions.

### Widget

A reusable presentation component embedded in one or more scenes.

### Presence

The consistent visual, audible, and interactive expression of Velvet's current body and conversational state.

### Module

A bounded optional package that may contribute scenes, widgets, assets, adapters, and approved request definitions without modifying the stable core or gaining direct authority.

## Features

- **Surface-agnostic scenes** for Qt, web, mobile, and custom surfaces
- **Scene navigation** with history and lifecycle management
- **Image-based scenes** defined through YAML
- **Polygon regions** with point-in-polygon hit testing
- **Automatic scaling** from base resolution to target display
- **Scene transitions** including fade and slide effects
- **Reusable widgets** across compatible surfaces
- **Ambient presence** designed to recede when not needed
- **Module-ready architecture** for optional capabilities above the stable system
- **Minimal core dependencies** with PyYAML as the scene loader dependency
- **Typed Python interfaces** for framework contracts

## Installation

### Core Framework

```bash
pip install velvet-interface
```

### Qt Support

```bash
pip install velvet-interface[qt]
```

### Development

```bash
pip install velvet-interface[dev]
```

## Quick Start

```python
import sys
from PyQt5.QtWidgets import QApplication

from velvet_interface.core import Router
from velvet_interface.scenes import SettingsScene
from velvet_interface.surfaces.pyqt import QtSurface

app = QApplication(sys.argv)
surface = QtSurface(800, 600)
surface.initialize()
router = Router(surface)
router.register_scene(SettingsScene())
router.navigate("settings")
surface.get_container().show()
sys.exit(app.exec_())
```

## Image Scene Example

```yaml
name: "home"
base_resolution: [1280, 720]
background: "assets/home.png"

regions:
  - name: "drive_entry"
    polygon: [[80, 280], [380, 280], [380, 430], [80, 430]]
    action: "navigate:drive"
    metadata:
      tooltip: "Enter Drive"

transitions:
  enter: "fade"
  exit: "fade"
```

A polygon may navigate within Interface or create a bounded route request. It must never encode a raw executor or hardware command.

## Supported Surfaces

### Qt

- Status: implemented
- Use cases: Founder display, desktop development, embedded surfaces
- Optional dependency: `PyQt5`

### Web

- Status: planned
- Use cases: browser and local-network presentation
- Boundary: presentation and bounded requests only

### Mobile

- Status: planned in this framework; companion work may exist separately
- Use cases: owner companion, status, receipts, bounded requests
- Boundary: remote presence never equals verified local physical presence

### Custom Surfaces

Custom renderers may subclass `Surface`. A custom renderer remains presentation code and does not inherit execution authority.

## Example Applications

The repository includes examples for:

- desktop scenes
- automotive layouts
- mobile presentation
- industrial HMIs
- robotics presentation

Examples demonstrate rendering patterns. They do not establish production hardware authority.

## Repository Shape

```text
velvet-interface/
├── velvet_interface/
│   ├── core/              # scene, surface, router, widget contracts
│   ├── scene_system/      # YAML and image-scene support
│   ├── scenes/            # reusable scenes
│   └── surfaces/          # Qt and future rendering adapters
├── assets/                # interface artwork where present
├── docs/                  # architecture and scene contracts
├── examples/              # demonstration applications
├── tests/                 # framework tests
└── README.md
```

Exact folders may evolve while the package remains alpha. Contributors should inspect the current tree before adding files.

## Development Laws

Before submitting changes:

- keep Interface non-authoritative
- preserve image-first and contextual-control behavior
- make presence states evidence-backed
- keep critical and accessible controls discoverable
- add capabilities through bounded scenes and modules
- do not place business or hardware logic inside rendering code
- do not let UI state masquerade as Runtime state
- preserve owner, guest, service, silent, and emergency separation
- add tests for routing, lifecycle, scaling, and safety boundaries
- update scene and module documentation when contracts change

## Documentation

- [Scene Interface Contract](docs/scene_interface_contract.md)
- [Architecture Guide](docs/architecture.md)
- [Creating Scenes](docs/creating-scenes.md)
- [Surface Development](docs/surfaces/)

## Requirements

- Python 3.8 or later
- PyYAML 5.4 or later for scene loading
- optional PyQt5 5.15 or later for Qt rendering
- no required cloud dependency

## Completed Foundation

- surface abstraction
- scene lifecycle and routing
- YAML image scenes
- polygon interaction regions
- scaling and transitions
- Qt presentation
- multiple demonstration surfaces
- public scene interface contract
- explicit Interface-versus-Runtime authority boundary

## Next Milestones

1. Define a stable presence-state contract and event mapping.
2. Refine living-space lifecycle and body-aware scene context.
3. Define bounded scene and module manifests.
4. Add reviewed plugin loading without expanding authority.
5. Add receipt-backed status and execution timelines.
6. Improve owner, guest, service, silent, and emergency presentation contracts.
7. Add adaptive and multi-display layouts.
8. Connect future optional modules to a dedicated modules repository when it exists.
9. Validate the image-first Founder experience on physical hardware.

## Project Status

**Version:** 0.2.0 alpha  
**Stability:** experimental; APIs may change

Production physical control is not provided by this repository.

## License

GPLv3. See [LICENSE](LICENSE).
