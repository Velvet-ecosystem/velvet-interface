# Founder Work Desk: protected visual ghost scene

The scene named velour_workdesk is registered by default but can only show data
after the existing owner-present AND maintenance-unlocked presentation
gate passes. It is linked from the hidden Owner Maintenance panel. The screen
has one local refresh and a Back control; it has no external links, network
handlers, GitHub credentials, merge buttons or actuation authority.

The bridge reads the Runtime Work Desk contract from an explicitly configured
local file. Missing Runtime package, missing file or invalid snapshot fails
closed to UNAVAILABLE. A ghost report displays GHOST prominently, and stale
snapshots display STALE. Source URLs are plain text, not active navigation.

Commissioning when the two proposed PRs have merged:

1. In the Runtime checkout, use the validated ghost fixture from
   examples/fixtures/founder_workdesk_ghost.json.
2. Supply an installed private local copy using --workdesk-snapshot PATH,
   or set VELVET_WORKDESK_SNAPSHOT_PATH.
3. Start Founder with no physical hardware connected, then use the existing
   hidden owner maintenance unlock and Open Velour Work Desk.
4. Verify that the v33 quota blocker is visible and that the panel is
   LOCKED when either owner presence or maintenance unlock is absent.
5. Confirm the report is read-only, no unknown status becomes trusted,
   and missing inputs produce UNAVAILABLE without accidental actuation.

This is a ghost-ready presentation integration, not live Gmail,
Calendar or GitHub access, and not production approval of the SQLite memory
shelf. The owner's real touch-point placement remains an on-device task.
