"""Export the Lab 1 guide as one self-contained HTML page (labs/lab1/guides/slides.html).

    python export_html.py OUTPUT.html

Uses the shared renderer's page builder through guide_lib, so the slides look like the PDF.
The page shows one slide at a time, scaled to the window: Right arrow, Space or Page Down for the next
slide, Left arrow or Page Up for the previous one, Home and End for the first and last, or click the
right or left half of the window. Printing the page prints every slide. The logos and pictures are
embedded; the fonts come from Google Fonts.
"""
import base64
import mimetypes
import os
import sys

import guide_lib
from guide_lib import H, HERE, W, render

SCREEN_CSS = """
@media screen{
html,body{width:100%;height:100%;overflow:hidden;background:#0b1220}
section{display:none!important;position:absolute;left:0;top:0;transform-origin:0 0}
section.on{display:flex!important}
}
"""

NAV_JS = """
(function () {
  var W = %d, H = %d;
  var slides = Array.prototype.slice.call(document.querySelectorAll('section'));
  var at = 0;
  function fit() {
    var s = Math.min(window.innerWidth / W, window.innerHeight / H);
    var el = slides[at];
    el.style.transform = 'scale(' + s + ')';
    el.style.left = Math.max(0, (window.innerWidth - W * s) / 2) + 'px';
    el.style.top = Math.max(0, (window.innerHeight - H * s) / 2) + 'px';
  }
  function show(i) {
    at = Math.max(0, Math.min(slides.length - 1, i));
    slides.forEach(function (s, n) { s.classList.toggle('on', n === at); });
    fit();
    history.replaceState(null, '', '#' + (at + 1));
  }
  document.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') { e.preventDefault(); show(at + 1); }
    else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); show(at - 1); }
    else if (e.key === 'Home') show(0);
    else if (e.key === 'End') show(slides.length - 1);
  });
  document.addEventListener('click', function (e) { show(e.clientX > window.innerWidth / 2 ? at + 1 : at - 1); });
  window.addEventListener('resize', fit);
  show(parseInt((location.hash || '#1').slice(1), 10) - 1 || 0);
})();
""" % (W, H)


def main(out):
    title, html = render.page(HERE)
    for path in set(guide_lib.blobs(HERE).values()):
        kind = mimetypes.guess_type(path)[0] or "image/png"
        with open(path, "rb") as f:
            data = f"data:{kind};base64," + base64.b64encode(f.read()).decode("ascii")
        html = html.replace(render.uri(path), data)
    assert "file:///" not in html, "a local file path is left in the page"
    html = html.replace("</style>", SCREEN_CSS + "</style>", 1)
    html = html.replace("</body>", f"<script>{NAV_JS}</script></body>", 1)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(f"{title}: {os.path.getsize(out) // 1024} KB written to {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "guide.html"))
