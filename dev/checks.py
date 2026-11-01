"""Regression checks run by `dev/run-harness.sh check` (real add-on code, real collection)."""
import json
import os
import re
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
    ok("fonts.googleapis.com" in html, "Google Fonts import kept for the default (Inter) stack")

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


def run_checks(col, load_addon, pick):
    check_html(col, load_addon, pick)
    check_store(col, load_addon, pick)
    check_dialog_state(col, load_addon, pick)
    check_translations(col, load_addon, pick)
    check_responsive(col, load_addon, pick)
    check_notetypes(col, load_addon, pick)
    print("\n{} check(s) failed".format(len(FAILS)) if FAILS else "\nall checks passed")
    for f in FAILS:
        print("  - " + f)
    return 1 if FAILS else 0
