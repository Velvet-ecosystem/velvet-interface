# F7: current Runtime evidence

Preflight success and saved systemctl status no longer assert initialized Runtime,
verified continuity or Court readiness. The Interface requires Runtime's
velvet.runtime.live_status.v1 record, with a current Linux boot ID, live PID and
matching process-start ticks, current session UUID, completed secure initialization,
known module health, false physical-control flags and timestamp age below ten seconds.
Missing, malformed, future, old-boot, dead-process and reused-PID evidence yields unknown.
Optional module failure yields degraded rather than active. Physical Control is DISABLED.

VELVET_RUNTIME_STATUS_PATH defaults to /opt/velvet/state/runtime_status.json on both
sides. The display requires local read permission and the same proc/boot namespace.
The record is local descriptive evidence protected by service filesystem permissions;
it is not remote attestation or execution permission. Audio may use a separate Python
3.11 process and does not share this Runtime lifecycle.

Presence READY additionally requires a bounded authority-free conversation health reply
with the same session UUID. An existing socket inode is insufficient. Old Runtime
producers that lack the live status/health operation display unknown or awake safely.
Merge the Runtime F7/F8 producer before this consumer. No persistent data migration.
