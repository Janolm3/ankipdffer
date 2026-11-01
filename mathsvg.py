"""MathJax (TeX) -> inline SVG, done before export because WeasyPrint runs no JavaScript.

Anki writes inline math as \\(...\\) and display math as \\[...\\]. Every formula of an export is
rendered once in a hidden Qt web page that loads the bundled MathJax 3 (SVG output without a font
cache, so each SVG is self-contained), and the TeX is replaced by the SVG. Sizes are converted to
em so a formula scales with the text around it, and it is drawn in the text colour. Formulas
MathJax cannot read are left as they were.
"""
import html as html_module
import json
import os
import re

from aqt.qt import QEventLoop, QTimer, QUrl

try:
    from aqt.qt import QWebEnginePage
except ImportError:  # pragma: no cover - Anki always ships WebEngine
    QWebEnginePage = None

MATHJAX_JS = os.path.join(os.path.dirname(__file__), ".vendor", "mathjax", "tex-svg-full.js")

_MATH_RE = re.compile(r"\\\((.+?)\\\)|\\\[(.+?)\\\]", re.S)
_SKIP_RE = re.compile(r"(<script\b.*?</script>|<style\b.*?</style>|<svg\b.*?</svg>)", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_EX_ATTR_RE = re.compile(r'\s(width|height)="(-?[\d.]+)ex"')
_VALIGN_RE = re.compile(r'style="vertical-align:\s*(-?[\d.]+)ex;?"')
EX_TO_EM = 0.5  # MathJax's default ex/em ratio

_cache = {}  # (tex, display) -> svg markup, or None when MathJax could not read it

_PAGE = """<!doctype html><html><head><meta charset="utf-8"><script>
window.MathJax = {
  svg: {fontCache: "none"},
  startup: {typeset: false},
  options: {enableAssistiveMml: false, enableMenu: false}
};
</script><script src="tex-svg-full.js"></script></head><body></body></html>"""

_RUN = """(function (items) {
  window.__pdfferMath = null;
  MathJax.startup.promise.then(function () {
    return Promise.all(items.map(function (it) {
      return MathJax.tex2svgPromise(it[0], {display: it[1]}).then(function (node) {
        var svg = node.querySelector("svg");
        var err = node.querySelector("[data-mjx-error]");
        return svg && !err ? svg.outerHTML : null;
      }).catch(function () { return null; });
    }));
  }).then(function (out) {
    window.__pdfferMath = JSON.stringify(out);
  }).catch(function (e) {
    window.__pdfferMath = JSON.stringify({error: String(e)});
  });
})(%s);"""


def available():
    return QWebEnginePage is not None and os.path.isfile(MATHJAX_JS)


def _tex(raw):
    """Field HTML inside the delimiters -> plain TeX (line breaks, tags and entities removed)."""
    text = re.sub(r"(?i)<br\s*/?>", " ", raw)
    return html_module.unescape(_TAG_RE.sub("", text)).strip()


def _formulas(html):
    """[(tex, display)] in the document text, skipping scripts, styles and existing SVG."""
    found = []
    for i, part in enumerate(_SKIP_RE.split(html)):
        if i % 2:
            continue
        for m in _MATH_RE.finditer(part):
            display = m.group(2) is not None
            tex = _tex(m.group(2) if display else m.group(1))
            if tex:
                found.append((tex, display))
    return found


def has_math(html):
    return ("\\(" in html or "\\[" in html) and bool(_formulas(html))


def _em(match):
    return ' {}="{:.3f}em"'.format(match.group(1), float(match.group(2)) * EX_TO_EM)


def _tidy(svg, display):
    """ex -> em sizes, wrapped in a span that carries the baseline shift.

    MathJax lowers a formula below the baseline with vertical-align on the <svg>; WeasyPrint
    ignores styles on an inline <svg>, which left formulas sitting too high (their descenders on
    the baseline). An inline-block wrapper whose bottom edge is shifted down does the same job.
    """
    svg = _EX_ATTR_RE.sub(_em, svg)
    shift = 0.0
    m = _VALIGN_RE.search(svg)
    if m:
        shift = float(m.group(1)) * EX_TO_EM
        svg = svg[:m.start()] + svg[m.end():]
    if display:
        return '<span class="mj mj-block">{}</span>'.format(svg)
    return '<span class="mj" style="vertical-align:{:.3f}em">{}</span>'.format(shift, svg)


def _render(items, timeout_s):
    """Render [(tex, display)] in a hidden page; returns {item: svg or None}."""
    if not items:
        return {}
    page = QWebEnginePage()
    loop = QEventLoop()
    state = {"out": None}

    def poll():
        page.runJavaScript("window.__pdfferMath || null", got)

    def got(value):
        if value:
            state["out"] = value
            loop.quit()
        else:
            QTimer.singleShot(40, poll)

    def loaded(ok):
        if not ok:
            loop.quit()
            return
        page.runJavaScript(_RUN % json.dumps([[tex, display] for tex, display in items]))
        QTimer.singleShot(40, poll)

    page.loadFinished.connect(loaded)
    page.setHtml(_PAGE, QUrl.fromLocalFile(os.path.dirname(MATHJAX_JS) + os.sep))
    QTimer.singleShot(int(timeout_s * 1000), loop.quit)
    loop.exec()
    page.loadFinished.disconnect(loaded)
    page.deleteLater()
    try:
        out = json.loads(state["out"]) if state["out"] else None
    except ValueError:
        out = None
    if not isinstance(out, list) or len(out) != len(items):
        return {}
    return {item: (_tidy(svg, item[1]) if svg else None) for item, svg in zip(items, out)}


def typeset(html, timeout_s=60):
    """Replace the TeX in `html` by SVG. Returns (html, rendered count, failed count)."""
    if not available():
        return html, 0, 0
    formulas = _formulas(html)
    if not formulas:
        return html, 0, 0
    todo = list(dict.fromkeys(f for f in formulas if f not in _cache))
    rendered = _render(todo, timeout_s)
    for item in todo:
        if item in rendered:  # a timeout leaves the item out, so it is retried next time
            _cache[item] = rendered[item]
    counts = {"ok": 0, "bad": 0}

    def sub(m):
        display = m.group(2) is not None
        key = (_tex(m.group(2) if display else m.group(1)), display)
        svg = _cache.get(key)
        if not svg:
            counts["bad"] += 1
            return m.group(0)
        counts["ok"] += 1
        return '<span class="mj-display">{}</span>'.format(svg) if display else svg

    parts = _SKIP_RE.split(html)
    for i in range(0, len(parts), 2):
        parts[i] = _MATH_RE.sub(sub, parts[i])
    return "".join(parts), counts["ok"], counts["bad"]
