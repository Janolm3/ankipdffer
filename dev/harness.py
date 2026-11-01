"""Headless dev harness for the AnkiPdffer add-on.

Runs the *real* add-on code against a throw-away Anki collection, offscreen,
so the dialog and the generated HTML can be inspected without launching Anki.

    dev/run-harness.sh                     # all scenarios -> dev/out/
    dev/run-harness.sh shots html pdf      # pick scenarios

Scenarios:
    shots  PNG screenshots of every dialog tab (light + dark)
    html   export HTML for each mode/layout combination
    pdf    real WeasyPrint export (needs python3.14 + pango, same as Anki)
    check  assertions on generated HTML (regression checks)
"""
import importlib.util
import os
import shutil
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "dev", "out")


def _make_png(path, color, text, size=(320, 200)):
    from PyQt6.QtGui import QColor, QFont, QImage, QPainter

    img = QImage(size[0], size[1], QImage.Format.Format_RGB32)
    img.fill(QColor(color))
    p = QPainter(img)
    p.setFont(QFont("Helvetica", 22))
    p.drawText(img.rect(), 0x84, text)  # AlignCenter
    p.end()
    img.save(path)


def build_collection(tmp):
    from anki.collection import Collection

    col = Collection(os.path.join(tmp, "collection.anki2"))
    media = col.media.dir()
    _make_png(os.path.join(media, "pic.png"), "#cfe3ff", "diagram")
    _make_png(os.path.join(media, "io.png"), "#e6f4d7", "anatomy", (480, 300))

    models = col.models
    basic = models.by_name("Basic")
    rev = models.by_name("Basic (and reversed card)")
    cloze = models.by_name("Cloze")
    io = models.by_name("Image Occlusion")
    if io is None:
        col.add_image_occlusion_notetype()
        io = models.by_name("Image Occlusion")

    # notetype with a hostile field name to exercise escaping
    weird = models.new("Weird <fields> & co")
    for name in ("Q <1>", "A & B"):
        models.add_field(weird, models.new_field(name))
    tmpl = models.new_template("Card 1")
    tmpl["qfmt"] = "{{Q <1>}}"
    tmpl["afmt"] = "{{FrontSide}}<hr id=answer>{{A & B}}"
    models.add_template(weird, tmpl)
    models.add(weird)
    weird = models.by_name("Weird <fields> & co")

    deck = col.decks.id("Pharma::Cardio")
    sub = col.decks.id("Pharma::Cardio::ACE")

    def add(model, did, **fields):
        n = col.new_note(model)
        for k, v in fields.items():
            n[k.replace("_", " ")] = v
        col.add_note(n, did)
        return n

    add(basic, deck, Front="What is an <b>ACE</b> inhibitor?",
        Back='Blocks conversion of angiotensin I.[sound:ace.mp3]<br><img src="pic.png">')
    add(basic, deck, Front="Captopril suffix?", Back="-pril")
    add(rev, sub, Front="Lisinopril", Back="ACE inhibitor")
    add(cloze, sub, Text="{{c1::Captopril}} is an {{c2::ACE inhibitor::class}} used in {{c1::hypertension}}.",
        Back_Extra="Short-acting.")
    add(io, deck,
        Image='<img src="io.png">',
        Occlusion="{{c1::image-occlusion:rect:left=.1:top=.1:width=.3:height=.25:oi=1}}"
                  "{{c2::image-occlusion:rect:left=.55:top=.5:width=.3:height=.3:oi=1}}",
        Header="Heart", Back_Extra="Two chambers hidden")
    add(weird, deck, **{"Q <1>": "weird q", "A & B": "weird a"})
    return col


def load_addon(col, dark=False):
    """Import the add-on with a fake `mw`, from a temp copy so repo files stay clean."""
    from PyQt6.QtWidgets import QApplication, QMenu, QWidget

    import aqt

    app = QApplication.instance() or QApplication(sys.argv)

    class FakePM:
        def night_mode(self):
            return dark

    class FakeForm:
        menuTools = QMenu()

    class FakeMW(QWidget):
        pass

    mw = FakeMW()
    mw.col = col
    mw.pm = FakePM()
    mw.form = FakeForm()
    aqt.mw = mw

    stage = tempfile.mkdtemp(prefix="pdffer-addon-")
    names = ["manifest.json", ".vendor"] + [f for f in os.listdir(REPO) if f.endswith(".py")]
    for name in names:
        os.symlink(os.path.join(REPO, name), os.path.join(stage, name))
    for mod in [m for m in sys.modules if m.startswith("pdffer_dev")]:
        del sys.modules[mod]
    spec = importlib.util.spec_from_file_location(
        "pdffer_dev", os.path.join(stage, "__init__.py"),
        submodule_search_locations=[stage])
    module = importlib.util.module_from_spec(spec)
    sys.modules["pdffer_dev"] = module
    spec.loader.exec_module(module)
    return app, mw, module, stage


def pick(dlg, deck):
    top = deck.split("::")[0]
    dlg.deck_combo.setCurrentIndex(dlg.deck_combo.findText(top))
    i = dlg.subdeck_combo.findData(deck)
    dlg.subdeck_combo.setCurrentIndex(i if i >= 0 else 0)


def scenario_shots(col):
    for dark in (False, True):
        app, mw, mod, stage = load_addon(col, dark)
        dlg = mod.PDFExportDialog(mw)
        pick(dlg, "Pharma::Cardio")
        dlg.show()
        app.processEvents()
        for i, name in enumerate(("content", "appearance", "page", "fields", "settings")):
            dlg.tabs.setCurrentIndex(i)
            app.processEvents()
            path = os.path.join(OUT, "shot-{}-{}.png".format(name, "dark" if dark else "light"))
            dlg.grab().save(path)
            print("wrote", path)
        # extra states: an expanded field row, and Cards mode (Fields tab hidden)
        dlg.tabs.setCurrentIndex(3)
        if dlg.field_widgets:
            dlg.field_widgets[0].adv_btn.click()
        app.processEvents()
        dlg.grab().save(os.path.join(OUT, "shot-fields-open-{}.png".format("dark" if dark else "light")))
        dlg.render_radio.setCurrentIndex(1)
        app.processEvents()
        dlg.grab().save(os.path.join(OUT, "shot-cards-mode-{}.png".format("dark" if dark else "light")))
        dlg.close()
        shutil.rmtree(stage, ignore_errors=True)


COMBOS = [
    # name, render (0 fields / 1 cards), build mode, widget tweaks {dotted.setter: value}
    ("fields-pdf", 0, "pdf", {}),
    ("fields-legacy", 0, "legacy", {}),
    ("cards-pdf", 1, "pdf", {}),
    ("cards-preview", 1, "preview", {}),
    ("fields-key-cloze-both", 0, "pdf", {"qa_combo.setCurrentIndex": 1, "cloze_combo.setCurrentIndex": 2}),
    ("fields-cloze-hide", 0, "pdf", {"cloze_combo.setCurrentIndex": 1}),
    ("cards-pages-io-all", 1, "pdf", {"qa_combo.setCurrentIndex": 2}),
    ("cards-io-each", 1, "pdf", {"io_combo.setCurrentIndex": 1}),
    ("cards-cloze-both", 1, "pdf", {"cloze_combo.setCurrentIndex": 2}),
    ("cards-pages-preview", 1, "preview", {"qa_combo.setCurrentIndex": 2}),
    ("cards-pages-preview-std", 1, "preview", {"qa_combo.setCurrentIndex": 2, "layout_radio.setCurrentIndex": 0}),
    ("fields-pagenum", 0, "pdf", {"page_numbers_cb.setChecked": True}),
]


def scenario_html(col):
    app, mw, mod, stage = load_addon(col)
    dlg = mod.PDFExportDialog(mw)
    results = {}
    for name, render, mode, tweaks in COMBOS:
        dlg._apply_settings(mod.DEFAULT_SETTINGS)
        pick(dlg, "Pharma::Cardio")
        dlg.render_radio.setCurrentIndex(render)
        for dotted, val in tweaks.items():
            obj = dlg
            *path, setter = dotted.split(".")
            for part in path:
                obj = getattr(obj, part)
            getattr(obj, setter)(val)
        mod.logger.start("harness")
        html, ids = dlg._build_html(mode=mode)
        path = os.path.join(OUT, "html-{}.html".format(name))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        results[name] = (html, ids)
        print("wrote", os.path.basename(path), "({} cards)".format(len(ids)))
    shutil.rmtree(stage, ignore_errors=True)
    return results


PDF_COMBOS = ["fields-pdf", "cards-pdf", "cards-pages-io-all", "fields-key-cloze-both", "fields-pagenum"]


def scenario_pdf(col):
    """Real WeasyPrint export of a few layouts (same engine Anki uses)."""
    app, mw, mod, stage = load_addon(col)
    dlg = mod.PDFExportDialog(mw)
    for name, render, mode, tweaks in COMBOS:
        if name not in PDF_COMBOS:
            continue
        dlg._apply_settings(mod.DEFAULT_SETTINGS)
        pick(dlg, "Pharma::Cardio")
        dlg.render_radio.setCurrentIndex(render)
        for dotted, val in tweaks.items():
            obj = dlg
            *path, setter = dotted.split(".")
            for part in path:
                obj = getattr(obj, part)
            getattr(obj, setter)(val)
        html, _ = dlg._build_html(mode="pdf")
        hp = os.path.join(stage, "in.html")
        with open(hp, "w", encoding="utf-8") as fh:
            fh.write(html)
        pdf = os.path.join(OUT, "export-{}.pdf".format(name))
        logs = []
        ok = dlg._export_pdf_via_weasyprint(pdf, hp, logs, dlg._font_debug_snapshot())
        print("pdf", os.path.basename(pdf), "ok" if ok else "FAILED", *[l for l in logs if "rror" in l or "xit" in l][:3])
        if ok and shutil.which("pdftoppm"):
            import subprocess
            subprocess.run(["pdftoppm", "-r", "60", "-png", pdf,
                            os.path.join(OUT, "pg-" + name)], check=False)
    shutil.rmtree(stage, ignore_errors=True)


def scenario_gallery():
    """dev/out/index.html: everything the other scenarios produced, on one page."""
    import html as h
    files = sorted(os.listdir(OUT))
    shots = [f for f in files if f.startswith("shot-")]
    pages = [f for f in files if f.startswith("pg-")]
    htmls = [f for f in files if f.startswith("html-") and f.endswith(".html")]
    pdfs = [f for f in files if f.endswith(".pdf")]
    out = ["<!doctype html><meta charset=utf-8><title>AnkiPdffer dev preview</title>",
           "<style>body{font:14px system-ui;margin:24px;background:#111;color:#eee}"
           "h1,h2{font-weight:600}img{max-width:100%;border:1px solid #333;border-radius:6px}"
           ".g{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:14px}"
           ".p{display:flex;flex-wrap:wrap;gap:10px}.p img{height:300px}a{color:#60a5fa}"
           "figure{margin:0}figcaption{color:#999;font-size:12px;padding:4px 0}</style>",
           "<h1>AnkiPdffer dev preview <small style='color:#888'>generated {}</small></h1>".format(
               __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"))]
    out.append("<h2>Dialog</h2><div class=g>")
    for f in shots:
        out.append("<figure><img src='{0}'><figcaption>{0}</figcaption></figure>".format(h.escape(f)))
    out.append("</div><h2>Exported PDF pages</h2><div class=p>")
    for f in pages:
        out.append("<figure><img src='{0}'><figcaption>{0}</figcaption></figure>".format(h.escape(f)))
    out.append("</div><h2>HTML exports</h2><ul>")
    for f in htmls:
        out.append("<li><a href='{0}'>{0}</a></li>".format(h.escape(f)))
    out.append("</ul><h2>PDFs</h2><ul>")
    for f in pdfs:
        out.append("<li><a href='{0}'>{0}</a></li>".format(h.escape(f)))
    out.append("</ul>")
    path = os.path.join(OUT, "index.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print("wrote", path)


def scenario_seed(base):
    """Create a ready-to-run Anki base folder: profile "User 1" (English UI) + the sample collection."""
    from pathlib import Path
    from aqt.profiles import ProfileManager

    base = os.path.abspath(base)
    os.makedirs(base, exist_ok=True)
    pm = ProfileManager(Path(base))
    pm.setupMeta()
    pm.create("User 1")
    pm.setLang("en")
    pm.set_last_loaded_profile_name("User 1")
    pm.meta["first_run"] = False
    pm.db.execute("update profiles set data = ? where name = ?", pm._pickle(pm.meta), "_global")
    pm.db.commit()
    pm.db.close()
    profile_dir = os.path.join(base, "User 1")
    os.makedirs(profile_dir, exist_ok=True)
    col = build_collection(profile_dir)
    col.close()
    print("seeded", base)


def main(argv):
    if argv and argv[0] == "seed":
        from PyQt6 import QtWebEngineWidgets  # noqa: F401
        from PyQt6.QtWidgets import QApplication
        _app = QApplication.instance() or QApplication(sys.argv)
        scenario_seed(argv[1])
        return
    which = argv or ["shots", "html", "pdf"]
    from PyQt6 import QtWebEngineWidgets  # noqa: F401  (must precede QApplication)
    from PyQt6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication(sys.argv)  # keep a reference alive
    os.makedirs(OUT, exist_ok=True)
    # remove only the files of the scenarios being re-run; everything else stays
    owned = {"shots": ("shot-",), "html": ("html-",), "pdf": ("export-", "pg-")}
    prefixes = tuple(p for name in which for p in owned.get(name, ()))
    for name in os.listdir(OUT):
        if prefixes and name.startswith(prefixes):
            os.remove(os.path.join(OUT, name))
    tmp = tempfile.mkdtemp(prefix="pdffer-col-")
    col = build_collection(tmp)
    try:
        if "shots" in which:
            scenario_shots(col)
        if "html" in which:
            scenario_html(col)
        if "pdf" in which:
            scenario_pdf(col)
        if "gallery" in which or not argv:
            scenario_gallery()
        if "check" in which:
            from checks import run_checks  # noqa: WPS433 (sibling module)
            sys.exit(run_checks(col, load_addon, pick))
    finally:
        col.close()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main(sys.argv[1:])
