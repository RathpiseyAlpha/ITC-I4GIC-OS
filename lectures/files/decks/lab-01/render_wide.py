"""Render the Lab 1 guide to PDF on its wider canvas, and audit it for overflow.

    python -X utf8 render_wide.py

Writes "Converted Slides/<deck title>.pdf" and lists every element outside the safe area.
"""
import os

import guide_lib

if __name__ == "__main__":
    guide_lib.render.render(os.path.basename(guide_lib.HERE))
