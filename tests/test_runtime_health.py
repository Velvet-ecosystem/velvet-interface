import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from velvet_interface.runtime_health import validate_live_status, process_start_ticks
from velvet_interface.boot_status import load_boot_snapshot, view_model_from_snapshot
from velvet_interface.conversation_bridge import UnixConversationBridge, _TRANSPORT_FLAGS
from velvet_interface.velvet_presence_live_status import load_velvet_presence_status


def status(**changes):
    value = dict(schema='velvet.runtime.live_status.v1', captured_at=100.0,
        boot_id='boot', session_id='00000000000040008000000000000001', pid=123,
        process_start_ticks=456, initialized=True, state='ready', modules_healthy=True,
        continuity_verified=True, court_ready=True, physical_control=False,
        grants_execution=False, grants_actuation=False)
    value.update(changes)
    return value


class RuntimeHealthTests(unittest.TestCase):
    def validate(self, value, **kw):
        return validate_live_status(value, now=100.0, boot_id='boot',
                                    process_probe=kw.get('process_probe', lambda pid: 456))

    def test_valid_current_boot_and_process_can_be_active(self):
        model = view_model_from_snapshot({'doctor': {'ready': True}}, live_status=status(),
            now=100.0, boot_id='boot', process_probe=lambda pid: 456)
        self.assertEqual(model.runtime, 'ACTIVE')
        self.assertEqual(model.continuity, 'VERIFIED')
        self.assertEqual(model.physical_control, 'DISABLED')

    def test_stale_future_dead_reused_pid_wrong_boot_missing_init_are_rejected(self):
        for changes in ({'captured_at': 90.0}, {'captured_at': 101.0},
                        {'captured_at': float('nan')}, {'boot_id': 'old-boot'},
                        {'process_start_ticks': 455}, {'state': 'stopped'},
                        {'initialized': False}, {'continuity_verified': False},
                        {'court_ready': False}, {'physical_control': True},
                        {'session_id': 'bad'}, {'pid': True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.validate(status(**changes))
        def missing(pid):
            raise ProcessLookupError('dead process')
        with self.assertRaises(ProcessLookupError):
            self.validate(status(), process_probe=missing)

    def test_readiness_projection_degrades_on_process_probe_failure(self):
        def missing(pid):
            raise ProcessLookupError('dead process')
        model = view_model_from_snapshot({'doctor': {'ready': True}}, live_status=status(),
            now=100.0, boot_id='boot', process_probe=missing)
        self.assertEqual(model.runtime, 'UNKNOWN')
        self.assertEqual(model.court, 'BLOCKED')

    def test_module_failure_is_degraded(self):
        model = view_model_from_snapshot({}, live_status=status(modules_healthy=False),
            now=100.0, boot_id='boot', process_probe=lambda pid: 456)
        self.assertEqual(model.runtime, 'DEGRADED')

    def test_loader_binds_to_real_proc_and_boot_then_rejects_old_session(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pid = int(Path('/proc/self/stat').read_text().split(' ', 1)[0])
            live = status(pid=pid, process_start_ticks=process_start_ticks(pid),
                          boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                          captured_at=time.time())
            (root/'boot.json').write_text(json.dumps({'doctor': {'ready': True}}))
            (root/'live.json').write_text(json.dumps(live))
            model = load_boot_snapshot(root/'boot.json', live_status_path=root/'live.json')
            self.assertEqual(model.runtime, 'ACTIVE')
            live['boot_id'] = 'previous-boot'
            (root/'live.json').write_text(json.dumps(live))
            model = load_boot_snapshot(root/'boot.json', live_status_path=root/'live.json')
            self.assertEqual(model.runtime, 'UNKNOWN')

    def test_health_reply_must_match_live_session_and_deny_authority(self):
        bridge = UnixConversationBridge('/unused', timeout_seconds=0.2)
        for changes, expected in (({}, True), ({'session_id': 'old'}, False),
                                  ({'physical_control': True}, False)):
            def reply(request):
                result = dict(schema='velvet.runtime.conversation_health.v1', session_id='current',
                    physical_control=False, grants_execution=False, grants_actuation=False)
                result.update(changes)
                return dict(protocol='velvet.runtime.unix.v1', kind='response',
                    request_id=request['request_id'], ok=True, result=result, **_TRANSPORT_FLAGS)
            with patch.object(bridge, '_call', side_effect=reply):
                self.assertEqual(bridge.health('current'), expected)

    def test_presence_requires_actual_matching_health_reply(self):
        active = SimpleNamespace(runtime='ACTIVE', session_id='current', message='active')
        with patch('velvet_interface.velvet_presence_live_status.load_boot_snapshot', return_value=active):
            with patch.object(UnixConversationBridge, 'health', return_value=True) as health:
                model = load_velvet_presence_status(Path('/unused'), Path('/unused.sock'))
                health.assert_called_once_with('current')
                self.assertEqual(model.state, 'READY')
            with patch.object(UnixConversationBridge, 'health', return_value=False):
                model = load_velvet_presence_status(Path('/unused'), Path('/unused.sock'))
                self.assertEqual(model.state, 'AWAKE')
