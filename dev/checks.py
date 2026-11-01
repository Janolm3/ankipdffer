"""Regression checks run by `dev/run-harness.sh check` (real add-on code, real collection)."""
import json
import os
import re
import time
import shutil
import tempfile

FAILS = []


def ok(cond, msg):
    print(("  ok    " if cond else "  FAIL  ") + msg)
    if not cond:
        FAILS.append(msg)


def strip_b64(html):
    return re.sub(r'data:[^"\']{40,}', "data:…", html)


def build(mod, dlg, pick, render, mode, tweaks=None):
    dlg._apply_settings(mod.DEFAULT_SETTINGS)
    pick(dlg, "Pharma::Cardio")
    dlg.render_radio.setCurrentIndex(render)
    for dotted, val in (tweaks or {}).items():
        obj = dlg
        *path, setter = dotted.split(".")
        for part in path:
            obj = getattr(obj, part)
        getattr(obj, setter)(val)
    mod.logger.start("check")
    html, _ = dlg._build_html(mode=mode)
    errors = [e for e in mod.logger.entries if "ERROR" in e]
    return strip_b64(html), errors


def check_html(col, load_addon, pick):
    app, mw, mod, stage = load_addon(col)
    dlg = mod.PDFExportDialog(mw)

    print("Fields mode")
    html, errs = build(mod, dlg, pick, 0, "pdf")
    ok(not errs, "no per-card errors ({})".format(errs[:1]))
    ok(html.count("Lisinopril") == 1, "reversed note exported once (no duplicate cards)")
    ok("{{c" not in html, "no raw {{cN::}} cloze markup")
    ok("image-occlusion:" not in html, "no raw image-occlusion markup")
    ok("[sound:" not in html and "[anki:play" not in html, "no [sound:] / [anki:play] leakage")
    ok("Q &lt;1&gt;" in html and "Q <1>" not in html, "field names are HTML-escaped")
    ok('class="io-m"' in html and 'class="io-o' in html, "IO note rendered with masks + outlines")
    ok('class="cz-a">Captopril' in html, "cloze revealed by default in Fields mode")

    html, _ = build(mod, dlg, pick, 0, "pdf", {"cloze_combo.setCurrentIndex": 1})
    ok('class="cz-h">[...]' in html and '[class]' in html, "cloze hidden as [...] / [hint]")
    ok('class="cz-a">Captopril' not in html, "hidden mode leaks no answers")

    html, _ = build(mod, dlg, pick, 0, "pdf", {"cloze_combo.setCurrentIndex": 2})
    ok('class="cz-h"' in html and 'class="cz-a"' in html, "hidden-then-revealed has both versions")

    print("Cards mode")
    html, errs = build(mod, dlg, pick, 1, "pdf")
    ok(not errs, "no per-card errors ({})".format(errs[:1]))
    ok("[anki:play" not in html, "no [anki:play] leakage")
    ok("<hr id=answer>" not in html, "no literal <hr id=answer>")
    ok("Toggle Masks" not in html and "<canvas" not in html, "no IO canvas/button leakage")
    ok(html.count('class="io-m"') == 2, "IO question: both masks drawn ({})".format(html.count('class="io-m"')))
    ok(html.count('class="io-n"') == 2, "IO answer: numbered outlines")
    ok(html.count("Lisinopril") == 2, "reversed note keeps its 2 cards natively")

    html, _ = build(mod, dlg, pick, 1, "pdf", {"io_combo.setCurrentIndex": 1})
    ok(html.count("io-wrap") >= 4, "one IO card per mask (>=2 pairs)")

    html, _ = build(mod, dlg, pick, 1, "pdf", {"cloze_combo.setCurrentIndex": 2})
    ok(html.count('class="cz-h"') >= 1 and 'class="cz-a"' in html, "cards-mode cloze: one entry hidden->revealed")

    print("Layouts")
    html, _ = build(mod, dlg, pick, 1, "pdf", {"qa_combo.setCurrentIndex": 2})
    n_breaks = html.count('class="page-break"')
    ok(n_breaks >= 8, "question page / answer page: {} page breaks".format(n_breaks))
    ok("#1 &middot; Answer" in html, "answer cards labelled")

    html, _ = build(mod, dlg, pick, 0, "pdf", {"qa_combo.setCurrentIndex": 1})
    heading = html.find('<h2 class="key-title">')
    ok(heading > html.find('<div class="card"') > 0, "answer key heading follows the questions")
    ok(html.count('class="page-break"') == 1, "exactly one break before the answer key")

    for mode in ("preview", "pdf_fallback"):
        for compact in (0, 1):
            html, errs = build(mod, dlg, pick, 1, mode,
                               {"qa_combo.setCurrentIndex": 2, "layout_radio.setCurrentIndex": compact})
            ok(not errs and "<body" in html, "{} / compact={} builds".format(mode, compact))

    print("Misc")
    html, _ = build(mod, dlg, pick, 0, "pdf", {"page_numbers_cb.setChecked": True})
    ok("@bottom-center" in html and "counter(pages)" in html, "page numbers CSS emitted")
    html, _ = build(mod, dlg, pick, 0, "pdf", {"font_combo.setCurrentIndex": 4})
    ok("fonts.googleapis.com" not in html, "Google Fonts import skipped for non-Inter stacks")
    html, _ = build(mod, dlg, pick, 0, "pdf")
    ok("fonts.googleapis.com" not in html, "System font does not fetch Google Fonts (works offline)")
    html, _ = build(mod, dlg, pick, 0, "pdf", {"font_combo.setCurrentIndex": 1})
    ok("fonts.googleapis.com" in html, "Inter font imports Google Fonts")

    dlg._apply_settings(mod.DEFAULT_SETTINGS)
    pick(dlg, "Pharma::Cardio")
    dlg.filter_edit.setText("tag:nonexistent")
    dlg._update_count()
    ok("No cards" in dlg.count_label.text(), "filter with no matches shows 'No cards'")
    dlg.filter_edit.setText("(((")
    dlg._update_count()
    ok(dlg.count_label.property("error") is True, "invalid search flagged")
    dlg.filter_edit.setText("")
    shutil.rmtree(stage, ignore_errors=True)


def check_store(col, load_addon, pick):
    print("Settings store")
    import importlib.util
    import sys
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location("pdffer_store", os.path.join(repo, "store.py"))
    store = importlib.util.module_from_spec(spec)
    sys.modules["pdffer_store"] = store
    spec.loader.exec_module(store)

    tmp = tempfile.mkdtemp(prefix="pdffer-store-")
    path = os.path.join(tmp, "settings.json")
    with open(path, "w") as fh:  # v1 flat file, as shipped before 1.4
        json.dump({"theme": 1, "language": "pl", "font_size": "15", "bogus": 1}, fh)
    st = store.SettingsStore(path)
    ok(st.settings["theme"] == 1 and st.settings["language"] == "pl", "v1 file migrated")
    ok(st.settings["font_size"] == 15 and "bogus" not in st.settings, "values coerced, unknown keys dropped")
    ok(st.settings["qa_layout"] == 0, "new options get defaults")

    st.set_field("Basic", "Front", {"section": 1, "bold": True, "size": 99})
    ok(st.fields["Basic"]["Front"]["size"] == 3, "field config clamped")
    ok(st.save() is None, "atomic save ok")
    st2 = store.SettingsStore(path)
    ok(st2.get_fields("Basic")["Front"]["bold"] is True, "per-note-type fields persist across reload")
    ok(st2.get_fields("Cloze") == {}, "other note types untouched")

    st2.update_settings({"theme": 2, "language": "de"})
    ok(st2.save_preset("Print compact"), "preset saved")
    st2.update_settings({"theme": 0})
    ok(st2.apply_preset("Print compact") and st2.settings["theme"] == 2, "preset restores options")
    ok(st2.settings["language"] == "de", "preset leaves the language alone")
    ok(st2.get_fields("Basic")["Front"]["bold"] is True, "preset restores fields")
    st2.reset_settings()
    st2.reset_fields()
    ok(st2.settings["theme"] == 0 and st2.fields == {}, "reset to defaults")
    ok(st2.settings["language"] == "de" and "Print compact" in st2.presets, "reset keeps language + presets")
    ok(st2.save_field_preset("FP", [("Front", {"bold": True}), ("Back", {"size": 0})]), "field preset saved")
    ok(st2.apply_field_preset("FP", "Cloze", ["Text", "Back Extra"]) == 2
       and st2.get_fields("Cloze")["Back Extra"]["size"] == 0, "field preset applies by position")
    st2.save()
    ok("FP" in store.SettingsStore(path).field_presets, "field presets persist")
    st2.delete_field_preset("FP")
    ok(st2.delete_preset("Print compact") and not st2.presets, "preset deleted")

    with open(path, "w") as fh:
        fh.write("{ not json")
    ok(store.SettingsStore(path).settings["theme"] == 0, "corrupt file falls back to defaults")
    shutil.rmtree(tmp, ignore_errors=True)


def check_dialog_state(col, load_addon, pick):
    print("Dialog persistence / singleton")
    app, mw, mod, stage = load_addon(col)
    dlg = mod.PDFExportDialog(mw)
    dlg.show()
    dlg.theme_radio.setCurrentIndex(2)
    dlg.qa_combo.setCurrentIndex(2)
    pick(dlg, "Pharma::Cardio")
    w = next(w for w in dlg.field_widgets if w.nt_name == "Basic" and w.field_name == "Back")
    w.section_combo.setCurrentIndex(0)
    dlg._flush_save()
    stored = json.load(open(os.path.join(stage, "settings.json")))
    ok(stored["settings"]["theme"] == 2 and stored["settings"]["qa_layout"] == 2, "options autosaved")
    ok(stored["fields"]["Basic"]["Back"]["section"] == 0, "field change saved under its note type")

    # switching decks must not lose per-note-type field settings
    pick(dlg, "Pharma::Cardio::ACE")
    pick(dlg, "Pharma::Cardio")
    w2 = next(w for w in dlg.field_widgets if w.nt_name == "Basic" and w.field_name == "Back")
    ok(w2.section_combo.currentIndex() == 0, "field settings survive switching decks")

    # reset a single note type
    dlg._reset_note_type("Basic")
    w3 = next(w for w in dlg.field_widgets if w.nt_name == "Basic" and w.field_name == "Back")
    ok(w3.section_combo.currentIndex() == 1, "note type reset restores its defaults")

    # one window: second 'open' returns the same instance, restores minimized state
    first = mod._get_dialog()
    first.showMinimized()
    mod.show_export_dialog()
    again = mod._get_dialog()
    ok(first is again, "the same window object is reused")
    ok(not again.isMinimized(), "minimized window is restored, not duplicated")

    # reopening a fresh dialog restores the saved options
    dlg2 = mod.PDFExportDialog(mw)
    ok(dlg2.theme_radio.currentIndex() == 2 and dlg2.qa_combo.currentIndex() == 2,
       "new dialog starts from the saved options")
    shutil.rmtree(stage, ignore_errors=True)


def check_translations(col, load_addon, pick):
    print("Translations")
    app, mw, mod, stage = load_addon(col)
    en = mod._STRINGS["en"]
    for code in mod.LANGUAGES:
        table = mod._STRINGS.get(code, {})
        missing = [k for k in en if k not in table]
        used_missing = [k for k in missing if k not in ("busy_hint", "msg_settings_saved", "msg_settings_err",
                        "msg_no_settings", "msg_settings_loaded", "msg_settings_load_err", "msg_settings_reset",
                        "btn_save_settings", "btn_load_settings", "lang_hint")]
        ok(code == "en" or len(used_missing) <= 3,
           "{}: {} keys fall back to English ({})".format(code, len(missing), used_missing[:4]))
    for code in mod.LANGUAGES:
        mod._set_language(code)
        d = mod.PDFExportDialog(mw)
        ok(d.windowTitle() != "" and d.export_btn.text() != "", "{}: dialog builds".format(code))
        d.deleteLater()
    mod._set_language("en")
    shutil.rmtree(stage, ignore_errors=True)


def check_responsive(col, load_addon, pick):
    print("Responsive window")
    app, mw, mod, stage = load_addon(col)
    from aqt.qt import QApplication, QPoint
    from PyQt6.QtTest import QTest
    dlg = mod.PDFExportDialog(mw)
    pick(dlg, "Pharma::Cardio")
    dlg.show()
    dlg.tabs.setCurrentIndex(3)
    QApplication.processEvents()
    mn = dlg.minimumSize()
    ok(mn.width() <= 640 and mn.height() <= 480, "window can shrink to {}x{}".format(mn.width(), mn.height()))

    dlg.resize(1100, 720)
    QApplication.processEvents()
    ok(not any(w._compact for w in dlg.field_widgets), "wide window: one-line field rows")
    row = dlg.field_widgets[0]
    header = next(h for h in dlg._nt_headers if isinstance(h, mod.FieldTableHeader))
    sec_x = row.section_combo.mapTo(dlg, QPoint(0, 0)).x()
    cap = header.layout().itemAt(2).widget()
    cap_x = cap.mapTo(dlg, QPoint(0, 0)).x()
    ok(abs(sec_x - cap_x) <= 1, "column header lines up with the rows ({} vs {})".format(sec_x, cap_x))
    right = row.adv_btn.mapTo(dlg, QPoint(row.adv_btn.width(), 0)).x()
    table = row.parentWidget()
    ok(right <= table.mapTo(dlg, QPoint(table.width(), 0)).x(), "row controls stay inside the table")

    dlg.resize(1, 1)
    QApplication.processEvents()
    ok(all(w._compact for w in dlg.field_widgets), "narrow window: two-line field rows")
    right = row.label_col.mapTo(dlg, QPoint(row.label_col.width(), 0)).x()
    ok(right <= row.mapTo(dlg, QPoint(row.width(), 0)).x(), "compact row is not clipped")

    row.export_cb.setChecked(False)
    ok(not row.section_combo.isEnabled() and not row.size_radio.isEnabled(),
       "unchecked field greys out its settings")
    row.export_cb.setChecked(True)

    QTest.keyClick(dlg, mod.Qt.Key.Key_2, mod.Qt.KeyboardModifier.ControlModifier)
    ok(dlg.stack.currentIndex() == 1, "Ctrl/Cmd+2 switches to the second tab")
    dlg._flush_save()
    dlg2 = mod.PDFExportDialog(mw)
    ok(dlg2.stack.currentIndex() == 1, "last tab is restored")
    dlg.render_radio.setCurrentIndex(1)
    QTest.keyClick(dlg, mod.Qt.Key.Key_4, mod.Qt.KeyboardModifier.ControlModifier)
    ok(dlg.stack.currentIndex() != 3, "hidden Fields tab cannot be reached by shortcut")
    dlg.close()
    dlg2.close()
    shutil.rmtree(stage, ignore_errors=True)


def check_notetypes(col, load_addon, pick):
    print("Note type editor / field presets")
    app, mw, mod, stage = load_addon(col)
    dlg = mod.PDFExportDialog(mw)
    pick(dlg, "Pharma::Cardio")
    shown = lambda: {w.nt_name for w in dlg.field_widgets}
    ok(shown() == {"Basic"}, "most used note type of the deck is edited first ({})".format(shown()))
    ok(dlg.nt_source.text() == mod._t("nt_detect_deck"), "source hint: most used in deck")

    # the card under review decides which type is shown when the window opens
    cloze = col.models.by_name("Cloze")

    class FakeCard:
        def note_type(self):
            return cloze

    class FakeReviewer:
        card = FakeCard()

    mw.state, mw.reviewer = "review", FakeReviewer()
    dlg.refresh_collection()
    ok(shown() == {"Cloze"}, "current card's note type is detected ({})".format(shown()))
    ok(dlg.nt_source.text() == mod._t("nt_detect_card"), "source hint: current card")
    mw.state = "deckBrowser"

    # any note type can be picked and edited, also one the deck does not use
    i = dlg.nt_combo.findText("Basic (optional reversed card)")
    ok(i >= 0, "note types outside the deck are listed")
    dlg.nt_combo.setCurrentIndex(i)
    dlg.nt_combo.activated.emit(i)
    ok(shown() == {"Basic (optional reversed card)"}, "picked note type is shown")
    ok(dlg.nt_source.text() == mod._t("nt_not_in_deck"), "source hint: not used in deck")
    row = next(w for w in dlg.field_widgets if w.field_name == "Back")
    row.size_radio.setCurrentIndex(3)
    dlg._flush_save()
    ok(mod._store.get_fields("Basic (optional reversed card)")["Back"]["size"] == 3,
       "edits are saved under the picked note type")

    # field presets: save from Basic, apply to Cloze (no common names -> by position)
    i = dlg.nt_combo.findData(col.models.by_name("Basic")["id"])
    dlg.nt_combo.setCurrentIndex(i)
    dlg.nt_combo.activated.emit(i)
    front = next(w for w in dlg.field_widgets if w.field_name == "Front")
    front.size_radio.setCurrentIndex(0)
    front.underline_cb.setChecked(True)
    ok(dlg._save_field_preset("Tiny front"), "field preset saved")
    ok("Tiny front" in mod._store.field_presets, "field preset stored")
    i = dlg.nt_combo.findData(cloze["id"])
    dlg.nt_combo.setCurrentIndex(i)
    dlg.nt_combo.activated.emit(i)
    ok(dlg._apply_field_preset("Tiny front") == 2, "preset applied to another note type")
    text = next(w for w in dlg.field_widgets if w.field_name == "Text")
    ok(text.size_radio.currentIndex() == 0 and text.underline_cb.isChecked(),
       "fields matched by position, rows refreshed")
    dlg._fill_field_preset_menu()
    titles = [a.text() for a in dlg.field_preset_menu.actions()]
    ok("Tiny front" in titles, "presets listed in the menu")

    # export uses the remembered config of a note type that is not on screen
    i = dlg.nt_combo.findData(col.models.by_name("Basic")["id"])
    dlg.nt_combo.setCurrentIndex(i)
    dlg.nt_combo.activated.emit(i)
    fc = dlg._collect_fc()
    ok(fc.get(cloze["id"], {}).get("Text", {}).get("underline") is True,
       "export keeps settings of note types not shown")
    ok(dlg._delete_field_preset("Tiny front", confirm=False) and not mod._store.field_presets,
       "field preset deleted")

    io = next(x for x in col.models.all_names_and_ids() if "Occlusion" in x.name)
    i = dlg.nt_combo.findData(io.id)
    dlg.nt_combo.setCurrentIndex(i)
    dlg.nt_combo.activated.emit(i)
    ok(not dlg.field_preset_btn.isEnabled() and not dlg.field_widgets,
       "Image Occlusion: presets off, automatic layout note")
    dlg.close()
    shutil.rmtree(stage, ignore_errors=True)


def check_141(col, load_addon, pick):
    print("1.4.1: pagination, links, strip, preview, engine, loader")
    app, mw, mod, stage = load_addon(col)
    dlg = mod.PDFExportDialog(mw)

    def html_for(deck, **tweaks):
        dlg._apply_settings(mod.DEFAULT_SETTINGS)
        pick(dlg, deck)
        for dotted, val in tweaks.items():
            obj = dlg
            *path, setter = dotted.split("__")
            for part in path:
                obj = getattr(obj, part)
            getattr(obj, setter)(val)
        mod.logger.start("check")
        return dlg._build_html(mode="pdf")[0]

    html = html_for("Lab::Long", layout_radio__setCurrentIndex=1)
    uids = re.findall(r'<div class="card[^"]*"[^>]*data-u="(\d+)"', html)
    ok(len(uids) == 60 and len(set(uids)) == 60, "every card carries a unique id for the layout pass")
    ok(dlg._last_layout == {"gap_ratio": 0.12, "min_split": 0.25}, "compact: tight gap limit")
    ok(".fb{" in html and "break-inside:avoid" in html.split(".fb{", 1)[1][:120], "fields never split")
    ok(".sec-div,.fl{break-after:avoid" in html, "header/divider/label stay with what follows")
    ok("box-decoration-break:clone" in html, "split cards keep their frame on both pages")
    ok(".fv a,.rs a{color:" in html and "text-decoration:none" in html, "links styled (no default blue underline)")
    ok("<details open" in html and "summary" in html, "<details> exported open, summary styled")
    footer = html.split("@bottom-right{content:\"", 1)[1].split('"', 1)[0]
    ok(footer.startswith("AnkiPdffer") and "Compact" in footer and "MCQ" in footer,
       "running footer names the generator and the note type ({})".format(footer))
    ok(".fv{font-size:inherit;orphans" in html and "overflow:hidden}" not in html.split(".fv{", 1)[1][:80],
       "fields no longer clip overflowing content")

    html = html_for("Lab::Long", layout_radio__setCurrentIndex=0)
    ok(dlg._last_layout["gap_ratio"] == 0.33, "standard: cards kept whole unless a third of a page is lost")
    html = html_for("Pharma::Cardio", qa_combo__setCurrentIndex=1)
    ok('data-keep="1"' in html, "forced breaks (answer key) are never back-filled")

    html = html_for("Lab::Long", strip_html_cb__setChecked=True)
    first = html.split('class="fl">Rationale</div>', 1)[1][:600]
    ok("<br>" in first and "<details" not in first, "strip formatting keeps line breaks")

    # Preview = the real PDF through the export path (no HTML mock-up)
    seen = {}
    dlg._start_external_export = lambda path: seen.update(path=path, html=open(dlg.temp_html_path).read())
    dlg._apply_settings(mod.DEFAULT_SETTINGS)
    pick(dlg, "Pharma::Cardio")
    dlg._on_preview()
    ok(seen.get("path", "").endswith(".pdf") and "AnkiPdffer-preview" in seen.get("path", ""),
       "Preview renders a temporary PDF")
    ok("page-break-marker" not in seen.get("html", "x") and "@page{size:" in seen.get("html", ""),
       "Preview uses the same HTML as Export")
    ok(dlg._preview_pending, "Preview opens without the 'saved' dialog")
    dlg._reset()

    # save dialog starts in a writable folder (last export folder, else Desktop)
    folder = dlg._export_dir()
    ok(os.path.isdir(folder) and os.access(folder, os.W_OK) and folder != "/",
       "save dialog starts in a writable folder ({})".format(folder))
    mod._store.update_settings({"export_dir": "/nonexistent/x"})
    ok(dlg._export_dir() != "/nonexistent/x", "a vanished export folder falls back to Desktop")
    mod._store.update_settings({"export_dir": ""})

    # loader: a floating HUD that stays in front while busy
    dlg.show()
    dlg._begin_busy("x")
    ok(dlg.busy_hud.isVisible() and dlg.busy_hud.isWindow(), "loader is a floating window while busy")
    ok(bool(dlg.busy_hud.windowFlags() & mod.Qt.WindowType.WindowStaysOnTopHint), "loader stays on top")
    v0 = dlg._busy_val
    for _ in range(50):
        dlg._animate_busy()
    ok(v0 < dlg._busy_val <= 95, "progress only grows ({} -> {:.0f})".format(v0, dlg._busy_val))
    dlg._end_busy(force=True)
    ok(not dlg.busy_hud.isVisible(), "loader hidden when done")

    # engine probe (the real one: imports WeasyPrint with the bundled vendor dir)
    report = dlg._engine_probe()
    ok(set(report) >= {"macos", "brew", "python", "pango", "engine"}, "engine probe reports every part")
    mod._store.update_settings({"engine_state": "ok"})
    dlg._engine_report = None
    dlg._show_engine_status()
    label = dlg.engine_status.text()
    ok(mod._t("engine_ok") in label and "#34c759" in label and dlg.engine_status.objectName() == "Secondary",
       "engine status: last known result at once, quiet text, only the dot is green")
    dlg._check_engine()
    ok(dlg.engine_status.text() == label and dlg.engine_check_btn.isEnabled(),
       "automatic re-check is silent (no 'Checking…', button stays enabled)")
    started = time.time()
    while dlg._engine_thread is not None and time.time() - started < 90:
        app.processEvents()
        time.sleep(0.05)
    ok(mod._store.settings["engine_state"] in ("ok", "missing") and "engine_state" in mod.MACHINE_KEYS,
       "check result remembered for the next session ({})".format(mod._store.settings["engine_state"]))
    css = mod.macui.stylesheet(False)
    ok(dlg.reset_btn.objectName() == "Destructive" and "QPushButton#Destructive {" not in css
       and "background: #bf5a54" in css.split("QPushButton#Destructive:hover {", 1)[1][:80],
       "Reset everything looks like any button and fills muted red only on hover")
    dialog = mod.EngineSetupDialog(dlg)
    ok("brew install python@3.14 pango" in dialog.commands()[1], "setup guide offers the brew command")
    dialog.reject()
    dlg.close()
    shutil.rmtree(stage, ignore_errors=True)


def check_overview_button(col, load_addon, pick):
    print("Deck screen: Export to PDF button")
    app, mw, mod, stage = load_addon(col)
    from types import SimpleNamespace

    study = ('<button id="study" class="but " onclick="pycmd(\'study\');return false;"\n'
             'title="" autofocus>Study Now</button>')
    table = ('<table width=400 cellpadding=5><tr><td align=center valign=top>counts</td>'
             '<td align=center>\n' + study + '</td></tr></table>')
    other_addon = '<div class="heatmap">stats from another add-on</div>'
    content = SimpleNamespace(table=table + other_addon)
    mod._on_overview_content(None, content)
    t = content.table
    ok(t.startswith(table) and t.index('<div id="ankipdffer-overview"') == len(table)
       and t.endswith(other_addon),
       "button sits right below the counts / Study Now table, above other add-ons")
    ok("pycmd('ankipdffer:export')" in t and "<svg" in t, "button sends the export command, crisp SVG icon")
    ok('tabindex="-1"' in t and 'onmousedown="event.preventDefault()"' in t,
       "button never takes focus, so Enter keeps starting Study Now")
    ok("%" not in mod._overview_button_html(), "no '%' (Anki fills the deck page with %-formatting)")
    ok(all(not d["btn_overview_pdf"].endswith(("…", "...")) for d in mod._EXTRA_STRINGS.values()),
       "button label has no ellipsis in any language")
    ok(".pdffer-btn{" in t and "border-radius:5px" in t and ".night-mode #ankipdffer-overview" in t,
       "OS X push-button style with a dark variant")
    content = SimpleNamespace(table="<table><tr><td>reshaped by another add-on</td></tr></table>")
    mod._on_overview_content(None, content)
    ok(content.table.endswith("</button></div>"), "unknown layouts get the button below the table")

    mod._set_overview_button(False)
    content = SimpleNamespace(table=table)
    mod._on_overview_content(None, content)
    ok(content.table == table, "switched off in Settings: deck screen untouched")
    mod._set_overview_button(True)
    ok("overview_button" in mod.MACHINE_KEYS, "button switch is not part of option presets")

    ok(mod._on_js_message((False, None), "study", None) == (False, None), "other bridge commands untouched")
    col.decks.select(col.decks.id_for_name("Pharma::Cardio"))
    handled = mod._on_js_message((False, None), mod.OVERVIEW_CMD, None)
    ok(handled == (True, None) and mod._dlg is not None and mod._dlg._sel() == "Pharma::Cardio",
       "button opens the window on the deck being viewed")
    col.decks.select(col.decks.id_for_name("Lab::Long"))
    mod._on_js_message((False, None), mod.OVERVIEW_CMD, None)
    ok(mod._dlg._sel() == "Lab::Long", "an open window switches to the newly viewed deck")

    # opening must build the field table once, not once per combo-box signal
    loads = []
    original = mod.PDFExportDialog._load_fields
    mod.PDFExportDialog._load_fields = lambda self: (loads.append(1), original(self))[1]
    try:
        mod._dlg.hide()
        col.decks.select(col.decks.id_for_name("Pharma::Cardio"))
        mod._on_js_message((False, None), mod.OVERVIEW_CMD, None)
        ok(len(loads) == 1 and mod._dlg._sel() == "Pharma::Cardio",
           "reopening on another deck builds the field table once ({}x)".format(len(loads)))
        mod._dlg.close()
        mod._dlg = None
        loads.clear()
        mod._on_js_message((False, None), mod.OVERVIEW_CMD, None)
        ok(len(loads) == 1, "a new window builds the field table once ({}x)".format(len(loads)))
    finally:
        mod.PDFExportDialog._load_fields = original
    mod._dlg.close()
    shutil.rmtree(stage, ignore_errors=True)


def check_windows(col, load_addon, pick):
    """The Windows engine setup, simulated on this machine: platform switched, a fake MSYS2 and a
    fake engine environment on disk, real QProcess runs for the install step queue."""
    import sys
    import time
    print("Windows PDF engine (simulated)")
    app, mw, mod, stage = load_addon(col)
    dlg = mod.PDFExportDialog(mw)
    fake = tempfile.mkdtemp(prefix="pdffer-win-")
    saved = {name: getattr(mod, name) for name in ("_engine_platform", "_win_python_candidates", "QDesktopServices")}
    saved_env = {k: os.environ.get(k) for k in ("ANKI_PDFFER_MSYS2", "WEASYPRINT_DLL_DIRECTORIES", "ANKI_PDFFER_PYTHON")}

    def wait(cond, seconds=60):
        end = time.time() + seconds
        while not cond() and time.time() < end:
            app.processEvents()
            time.sleep(0.02)
        return cond()

    opened = []

    class FakeDesktop:
        @staticmethod
        def openUrl(url):
            opened.append(url.toString())
            return True

    try:
        ok(dlg._engine_vendor_dir() == dlg._vendor_dir(), "macOS keeps the bundled vendor dir")
        mod._engine_platform = lambda: "windows"
        mod.QDesktopServices = FakeDesktop
        mod._win_python_candidates = lambda: [["/nonexistent/python.exe"], ["/usr/bin/false"], [sys.executable]]
        for k in saved_env:
            os.environ.pop(k, None)
        os.environ["ANKI_PDFFER_MSYS2"] = fake
        ok(dlg._engine_vendor_dir() == "", "Windows never loads the macOS-only vendor dir")
        ok(mod._msys2_bash() is None and mod._win_dll_dirs() == [], "no MSYS2 yet: nothing detected")

        bash = os.path.join(fake, "usr", "bin", "bash.exe")
        dll_dir = os.path.join(fake, "ucrt64", "bin")
        for path in (bash, os.path.join(dll_dir, mod.WIN_PANGO_DLL)):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "w").close()
        ok(mod._msys2_bash() == bash, "MSYS2 found in its root")
        ok(mod._win_dll_dirs() == [dll_dir], "Pango DLLs found in MSYS2's UCRT64 bin")
        env = dlg._isolated_python_env()
        ok(env.get("WEASYPRINT_DLL_DIRECTORIES") == dll_dir, "engine processes get WEASYPRINT_DLL_DIRECTORIES")
        ok(env.get("PATH") == os.environ.get("PATH"), "no Homebrew paths added on Windows")

        ok(mod._win_base_python() == sys.executable, "base Python found (broken candidates skipped)")
        ok(mod._win_engine_dir().startswith(os.path.join(stage, "user_files")),
           "engine environment lives in user_files (kept across updates)")
        ok(not mod._win_engine_installed(), "engine environment not installed yet")

        report = dlg._engine_probe()
        ok(set(report) >= {"platform", "winget", "python", "msys2", "pango", "venv", "engine"},
           "Windows probe reports every part")
        ok(report["platform"] == "windows" and report["pango"] == dll_dir and report["python"] == sys.executable
           and not report["venv"] and not report["engine"], "Windows probe: Python + Pango found, engine missing")

        dialog = mod.EngineSetupDialog(dlg)
        ok(list(dialog.rows) == ["python", "pango", "venv", "engine"], "setup guide shows the Windows parts")
        wait(lambda: getattr(dlg, "_engine_thread", None) is None and getattr(dialog, "report", None))
        marks = {k: m.text() for k, (m, _) in dialog.rows.items()}
        ok(marks == {"python": "\u2713", "pango": "\u2713", "venv": "\u2715", "engine": "\u2715"},
           "setup guide marks what is there ({})".format(marks))
        ok(dialog.install_btn.isEnabled(), "Install is offered on Windows")
        text = "\n".join(dialog.commands())
        ok("winget install -e --id Python.Python.3.13" in text and "MSYS2.MSYS2" in text
           and "mingw-w64-ucrt-x86_64-pango" in text and "weasyprint==68.1" in text,
           "Copy commands gives the Windows commands")

        nothing = {"platform": "windows", "winget": "C:\\winget.exe"}
        steps = dialog.windows_steps(nothing)
        commands = [make() for make, _ in steps]
        ok(len(steps) == 7 and commands[0][:5] == ["C:\\winget.exe", "install", "-e", "--id", "Python.Python.3.13"]
           and "--scope" in commands[0], "fresh Windows: Python, MSYS2, Pango, environment, WeasyPrint")
        ok(commands[2] == [bash, "-lc", " "] and commands[3][2].startswith("pacman -Syu")
           and [r for _, r in steps] == [False, False, False, False, True, True, True],
           "pacman runs twice, only the last run must succeed")
        ok(commands[5] == [sys.executable, "-m", "venv", "--clear", mod._win_engine_dir()]
           and commands[6][1:5] == ["-m", "pip", "install", "--disable-pip-version-check"],
           "engine environment made from the found Python, then WeasyPrint installed into it")
        ok(len(dialog.windows_steps(dict(report))) == 2, "Python + Pango present: only environment + WeasyPrint")
        ok("--force-reinstall" in dialog.windows_steps(dict(report, venv="x"))[0][0](),
           "all present but failing: WeasyPrint reinstalled")

        dialog._install_windows({"platform": "windows"})
        ok(len(opened) == 2 and "python.org" in opened[0] and "msys2.org" in opened[1]
           and dialog.note.text() == mod._t("eng_win_manual"), "no winget: download pages open instead")
        opened.clear()
        ran = []
        dialog._run_steps = lambda steps, message: ran.append((len(steps), message))
        dialog._install_windows(dict(report, winget=None))
        del dialog._run_steps
        ok(not opened and ran == [(2, mod._t("eng_win_running"))], "no winget needed when Python and MSYS2 exist")

        raw = b"Downloading\r 10%\r100%\r\n-\r\\\r|\rDone\n"
        ok(dialog.clean_output(raw) == "100%\nDone", "winget progress redraws are cleaned from the log")

        py = sys.executable
        dialog._run_steps([(lambda: [py, "-c", "print('step one')"], True),
                           (lambda: [py, "-c", "import sys; sys.exit(3)"], False),
                           (lambda: [py, "-c", "print('step three')"], True)], "x")
        wait(lambda: dialog.proc is None and not dialog.steps)
        log = dialog.log.toPlainText()
        ok("step one" in log and "[exit code 3]" in log and "step three" in log,
           "steps run in order; an optional step may fail")
        wait(lambda: getattr(dlg, "_engine_thread", None) is None)
        dialog._run_steps([(lambda: ["/nonexistent/winget.exe"], True),
                           (lambda: [py, "-c", "print('never')"], True)], "x")
        wait(lambda: dialog.proc is None and not dialog.steps)
        ok("never" not in dialog.log.toPlainText() and dialog.note.text() == mod._t("eng_failed"),
           "a required step that cannot start stops the install")
        wait(lambda: getattr(dlg, "_engine_thread", None) is None)
        dialog.reject()
        ok(dialog._closing and not dialog.steps, "closing the guide stops the install")

        venv_py = mod._win_engine_python()
        os.makedirs(os.path.dirname(venv_py), exist_ok=True)
        open(venv_py, "w").close()
        os.makedirs(os.path.join(mod._win_engine_dir(), "Lib", "site-packages", "weasyprint-68.1.dist-info"))
        ok(mod._win_engine_installed(), "engine environment detected by its pinned WeasyPrint")
    finally:
        for name, value in saved.items():
            setattr(mod, name, value)
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(fake, ignore_errors=True)
    dlg.close()
    shutil.rmtree(stage, ignore_errors=True)


def run_checks(col, load_addon, pick):
    check_html(col, load_addon, pick)
    check_store(col, load_addon, pick)
    check_dialog_state(col, load_addon, pick)
    check_translations(col, load_addon, pick)
    check_responsive(col, load_addon, pick)
    check_notetypes(col, load_addon, pick)
    check_141(col, load_addon, pick)
    check_overview_button(col, load_addon, pick)
    check_windows(col, load_addon, pick)
    print("\n{} check(s) failed".format(len(FAILS)) if FAILS else "\nall checks passed")
    for f in FAILS:
        print("  - " + f)
    return 1 if FAILS else 0
