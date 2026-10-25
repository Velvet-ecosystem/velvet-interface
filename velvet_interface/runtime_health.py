"""Validate descriptive local Runtime liveness, without granting authority."""
import math
from pathlib import Path
import time
from uuid import UUID

SCHEMA = 'velvet.runtime.live_status.v1'
MAX_AGE_SECONDS = 10.0


def process_start_ticks(pid):
    fields = Path('/proc/%d/stat' % pid).read_text().rsplit(') ', 1)[1].split()
    if fields[0] in ('Z', 'X', 'x'):
        raise ValueError('Runtime process is dead')
    return int(fields[19])


def validate_live_status(value, *, now=None, boot_id=None, process_probe=None):
    if not isinstance(value, dict) or value.get('schema') != SCHEMA:
        raise ValueError('Runtime initialization unverified: live status missing or invalid')
    captured = value.get('captured_at')
    if isinstance(captured, bool) or not isinstance(captured, (int, float)):
        raise ValueError('Runtime status timestamp invalid')
    age = (time.time() if now is None else now) - captured
    if not math.isfinite(age) or not 0 <= age < MAX_AGE_SECONDS:
        raise ValueError('Runtime status stale or future-dated')
    current_boot = boot_id if boot_id is not None else Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if value.get('boot_id') != current_boot or not current_boot:
        raise ValueError('Runtime status belongs to another boot')
    session = value.get('session_id')
    if not isinstance(session, str) or UUID(session).hex != session:
        raise ValueError('Runtime session identity invalid')
    pid = value.get('pid')
    ticks = value.get('process_start_ticks')
    if type(pid) is not int or pid <= 0 or type(ticks) is not int or ticks <= 0:
        raise ValueError('Runtime process identity invalid')
    if (process_probe or process_start_ticks)(pid) != ticks:
        raise ValueError('Runtime process absent or replaced')
    if value.get('physical_control') is not False or value.get('grants_execution') is not False or value.get('grants_actuation') is not False:
        raise ValueError('Runtime status attempted to grant physical control')
    if value.get('initialized') is not True or value.get('state') not in ('ready', 'degraded'):
        raise ValueError('Runtime initialization incomplete or stopped')
    if value.get('continuity_verified') is not True or value.get('court_ready') is not True:
        raise ValueError('Runtime secure initialization incomplete')
    if not isinstance(value.get('modules_healthy'), bool):
        raise ValueError('Runtime module health unknown')
    return value
