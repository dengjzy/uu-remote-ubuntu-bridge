#!/usr/bin/python3
"""Disposable Xlib window for the PR #19 review; never a real desktop."""

import os
import sys

from Xlib import X, display
from Xlib.ext import shape


tag = sys.argv[1]
x, y, width, height = map(int, sys.argv[2:6])
color = int(sys.argv[6], 16)
connection = display.Display()
screen = connection.screen()
window = screen.root.create_window(
    x, y, width, height, 0, screen.root_depth, X.InputOutput,
    X.CopyFromParent, background_pixel=color, override_redirect=True,
    event_mask=X.ButtonPressMask | X.PointerMotionMask,
)
window.set_wm_class(sys.argv[7], sys.argv[7])
window.set_wm_name(os.environ.get("FX_TITLE", tag))
if tag == "main" and os.environ.get("UURB_REVIEW_XSHAPE") == "1":
    window.shape_rectangles(
        shape.SO.Set, shape.SK.Bounding, X.Unsorted, 0, 0,
        [(0, 0, width - 100, height), (width - 100, 100, 100, height - 100)],
    )
window.map()
connection.sync()
print("ready", window.id, flush=True)
with open(os.environ["FX_LOG"], "a", buffering=1) as log:
    while True:
        event = connection.next_event()
        if event.type in (X.ButtonPress, X.MotionNotify):
            kind = "press" if event.type == X.ButtonPress else "motion"
            log.write(f"{tag} {kind} {event.root_x} {event.root_y}\n")
