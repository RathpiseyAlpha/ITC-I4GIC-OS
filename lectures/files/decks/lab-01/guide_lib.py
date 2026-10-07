"""Shared setup for rendering the Lab 1 guide: a wider canvas and pictures kept in the course repository.

The week decks are 1920 x 1080. This guide is wider (see size.json) so that it fills a laptop browser
window, and it keeps the pictures of the earlier Lab 1 guide, which live in labs/lab1/guides/images
(see images.json). Both differ from the shared renderer's defaults, so this module patches it.

The shared renderer is Cloud Computing/decks/render.py, two folders above this deck folder's parent.
Set GUIDE_REPO to the course repository when this folder is not inside it.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DECKS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(DECKS)), "Cloud Computing", "decks"))

import render  # noqa: E402

ROOT = os.environ.get("GUIDE_REPO") or os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


SIZE = load("size.json")
W, H = SIZE["width"], SIZE["height"]


def blobs(deck):
    """Map each asset id to its local file: the two logos, and the pictures listed in images.json."""
    pictures = load("images.json")
    out = {}
    for key, blob in load("assets.json").items():
        out[blob] = render.LOGOS.get(key) or os.path.join(ROOT, pictures[key].replace("/", os.sep))
    return out


_page = render.page


def page(deck):
    title, html = _page(deck)
    for old, new in (("size:1920px 1080px", f"size:{W}px {H}px"),
                     ("width:1920px;height:1080px;overflow:hidden", f"width:{W}px;height:{H}px;overflow:hidden"),
                     ("s.left - 1792", f"s.left - {W - 128}")):
        assert old in html, f"the shared renderer changed: {old!r} not found"
        html = html.replace(old, new)
    return title, html


render.blobs = blobs
render.page = page
render.HERE = DECKS
render.OUT = os.path.join(os.path.dirname(DECKS), "Converted Slides")
