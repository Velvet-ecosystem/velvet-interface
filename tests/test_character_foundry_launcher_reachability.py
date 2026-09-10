from __future__ import annotations

import os
from pathlib import Path
import unittest
from unittest.mock import patch

from velvet_interface.founder_surface_launcher import build_parser


class CharacterFoundryLauncherReachabilityTests(unittest.TestCase):
    def test_launcher_exposes_local_foundry_state_and_disable_flag(self):
        args = build_parser().parse_args([])
        self.assertEqual(
            args.foundry_state_dir,
            Path(".velvet-dev/persona-continuity"),
        )
        self.assertFalse(args.disable_character_foundry)

    def test_foundry_state_dir_can_be_bound_from_environment(self):
        with patch.dict(
            os.environ,
            {"VELVET_FOUNDRY_STATE_DIR": "/var/lib/velvet/persona"},
            clear=False,
        ):
            args = build_parser().parse_args([])
        self.assertEqual(args.foundry_state_dir, Path("/var/lib/velvet/persona"))

    def test_disable_character_foundry_flag_is_explicit(self):
        args = build_parser().parse_args(["--disable-character-foundry"])
        self.assertTrue(args.disable_character_foundry)


if __name__ == "__main__":
    unittest.main()
