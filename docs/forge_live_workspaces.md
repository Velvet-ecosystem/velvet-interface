# Founder Forge live workspaces

The Founder Forge uses the existing `workspace_scroll.png` artwork as the physical page and renders trusted data widgets as a transparent ink layer above it.

The design rule is intentional:

```text
scroll artwork
    + transparent presentation widget
    + invisible Back / Emergency press points
    = live Founder workspace
```

The workspace is not a mock page. It reads canonical local evidence when that evidence is available and fails visibly when it is not.

## Current live workspaces

### Engineering Design

`engineering_design` reads the configured Eleanor engineering project through two bounded seams:

1. `EleanorBridge.validate()` asks Eleanor's isolated CLI to validate the canonical project.
2. `EngineeringDesignBridge` safely re-reads the same bounded YAML manifest for presentation fields such as project identity, lifecycle, revision, intent, record counts, authority gate, and handoff recommendations.

The Interface does not duplicate Eleanor's engineering validator and does not alter the project manifest.

### Module Lab / Hardware Engineering

`module_lab` reads the canonical local `Modules` repository without importing candidate packages or executing candidate code.

The presentation inventory is limited to:

- candidate directories that contain a regular `SPEC.md`;
- lab intake evidence;
- lab report evidence;
- promoted module-domain directories.

The bridge rejects symlinked roots and applies bounded directory scans. A candidate's presence in the lab remains evidence of lifecycle state, not Runtime, Court, deployment, or hardware authority.

### Test Bench / Validation

`test_bench` asks the isolated Eleanor CLI for three read-only evidence sets:

```text
validate
validate --verify-artifacts
coverage
```

The second command re-reads registered engineering artifacts and compares their recorded hashes. It does not save or rewrite those artifacts.

Passing tests and validation are evidence only. They do not grant fabrication, vehicle-installation, machine-execution, or physical-control authority.

## Trusted widget registry

Image-surface manifests may request only exact IDs from the built-in allow-list:

```text
forge_engineering_design
forge_module_lab
forge_test_bench
```

A YAML surface cannot provide a Python import, shell command, executable path, or arbitrary widget factory. The trusted registry owns the code behind each identifier.

## Development posture

The standard development launcher sets:

```text
VELVET_INTERFACE_DEVELOPMENT=true
```

This changes presentation only. The scroll footer makes the development posture explicit:

```text
DEVELOPMENT • PRESENTATION AUTHORITY ONLY • PHYSICAL EXECUTION DISABLED
```

It does not synthesize owner presence, maintenance access, Court grants, Runtime capabilities, or physical authority.

The workspaces remain useful in development because their evidence paths are real. Development blocks consequential authority rather than replacing canonical data with demo values.

## Local source defaults

The trusted registry uses these defaults:

```text
VELVET_ELEANOR_EXECUTABLE=~/velvet/.venvs/eleanor/bin/eleanor-engineering
VELVET_ELEANOR_PROJECT=~/velvet/velvet-eleanor-engineering/projects/automotive-interface-io-v0/engineering-project.yaml
VELVET_MODULES_ROOT=~/velvet/Modules
```

Each may be overridden explicitly for another local workspace layout.

## Failure behavior

Missing repositories, manifests, executables, invalid schema, unsafe symlinks, oversized evidence, or unavailable Eleanor commands do not produce synthetic healthy state. The scroll reports canonical evidence as unavailable while the authority footer remains blocked.

## Future authority-bearing actions

These Founder pages are deliberately observation and validation surfaces today. Future design edits, promotion actions, fabrication releases, machine jobs, or hardware tests must enter through their owning domain's explicit authority contract. They must not be added by teaching the transparent presentation widget to mutate repository state or touch hardware directly.
