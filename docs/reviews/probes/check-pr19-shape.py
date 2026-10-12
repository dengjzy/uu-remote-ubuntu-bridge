#!/usr/bin/python3
"""Fail if PR #19's actual viewer exposes or clicks through an X Shape hole.

Usage: /usr/bin/python3 check-pr19-shape.py /path/to/pr19-checkout
The test intentionally fails on reviewed head 9ca86dc. It reuses that PR's
isolated harness and creates no production desktop/Wine connections.
"""

import os
import sys
import unittest
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit(__doc__)
checkout = Path(sys.argv[1]).resolve()
if not (checkout / "tests/test_window_region_isolation.py").is_file():
    raise SystemExit("Supply a PR #19 checkout containing its isolation tests.")
sys.path.insert(0, str(checkout / "tests"))
import test_window_region_isolation as harness  # noqa: E402

harness.FIXTURE = Path(__file__).with_name("pr19-shape-window.py")


class ShapeBoundary(harness.WindowRegionIsolationTests):
    def test_no_relay_pixels_or_clicks_through_shape(self):
        previous = os.environ.get("UURB_REVIEW_XSHAPE")
        os.environ["UURB_REVIEW_XSHAPE"] = "1"
        try:
            self.start_windows(("main", 100, 100, 900, 600, "00ff00"))
            client = self.open_window()
            self.click(client, 850, 50)
            colors = client.frame()
            presses = self.events("relay press")
            print({"relay_pixels": colors[harness.RED], "relay_clicks": presses,
                   "frame_size": [client.width, client.height]}, flush=True)
            self.assertEqual((0, []), (colors[harness.RED], presses),
                             "UU region exported or forwarded input to its underlying relay")
        finally:
            if previous is None:
                os.environ.pop("UURB_REVIEW_XSHAPE", None)
            else:
                os.environ["UURB_REVIEW_XSHAPE"] = previous


suite = unittest.TestSuite([ShapeBoundary("test_no_relay_pixels_or_clicks_through_shape")])
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful() or bool(result.skipped))
