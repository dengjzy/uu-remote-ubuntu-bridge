#!/usr/bin/python3
"""Compare -id with PR22's -sid on disposable X servers.

Usage: compare-pr22-capture.py /path/to/pr19-checkout /path/to/pr22-checkout
Uses PR19's isolated RFB harness and the adjacent plain-Xlib shape fixture.
Reports existing -id click-through too. Intentionally fails when -sid exports
underlying relay pixels; a passing harness run is not runtime acceptance.
"""

import os
import sys
import unittest
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit(__doc__)
pr19, pr22 = (Path(arg).resolve() for arg in sys.argv[1:])
sys.path.insert(0, str(pr19 / 'tests'))
import test_window_region_isolation as harness  # noqa: E402

harness.FIXTURE = Path(__file__).with_name('pr19-shape-window.py')
definitions = (pr22 / 'scripts/uu-remote-console').read_text().split(
    'case "${1:-open}" in', 1)[0]
if '-sid "$client_window"' not in definitions:
    raise SystemExit('Expected the reviewed PR22 -sid revision.')


class CaptureComparison(harness.WindowRegionIsolationTests):
    def compare(self, mode):
        harness.DEFINITIONS = definitions.replace(
            '-sid "$client_window"', f'-{mode} "$client_window"')
        previous = os.environ.get('UURB_REVIEW_XSHAPE')
        os.environ['UURB_REVIEW_XSHAPE'] = '1'
        try:
            self.start_windows(('main', 100, 100, 900, 600, '00ff00'))
            client = self.open_window(experimental=False)
            self.click(client, 850, 50)
            colors = client.frame()
            print({'mode': mode, 'relay_pixels': colors[harness.RED],
                   'relay_clicks': self.events('relay press'),
                   'frame_size': [client.width, client.height]}, flush=True)
            self.assertEqual(0, colors[harness.RED],
                             'Underlying desktop pixels exported through the shape hole')
        finally:
            if previous is None:
                os.environ.pop('UURB_REVIEW_XSHAPE', None)
            else:
                os.environ['UURB_REVIEW_XSHAPE'] = previous

    def test_existing_id(self):
        self.compare('id')

    def test_proposed_sid(self):
        self.compare('sid')


suite = unittest.TestSuite(CaptureComparison(name) for name in (
    'test_existing_id', 'test_proposed_sid'))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful() or bool(result.skipped))
