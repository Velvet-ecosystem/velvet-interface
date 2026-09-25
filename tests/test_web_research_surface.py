# SPDX-License-Identifier: GPL-3.0-only

from pathlib import Path
import unittest

import yaml


class WebResearchSurfaceTests(unittest.TestCase):
    def test_research_widget_stays_inside_reviewed_scroll_writing_area(self):
        path = Path("examples/surfaces/velour_web_research.surface.yaml")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        widgets = {item["widget_id"]: item for item in document["widgets"]}
        research = widgets["velour_web_research"]

        self.assertEqual(
            research["rect"],
            [0.175347, 0.195000, 0.647570, 0.575062],
        )
        self.assertEqual(document["metadata"]["physical_control"], "disabled")
        self.assertEqual(document["metadata"]["authority"], "none")
        self.assertEqual(document["metadata"]["network_adapter"], "disconnected")


if __name__ == "__main__":
    unittest.main()
