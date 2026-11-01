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


def run_checks(col, load_addon, pick):
    check_html(col, load_addon, pick)
    check_store(col, load_addon, pick)
    check_dialog_state(col, load_addon, pick)
    check_translations(col, load_addon, pick)
    print("\n{} check(s) failed".format(len(FAILS)) if FAILS else "\nall checks passed")
    for f in FAILS:
        print("  - " + f)
    return 1 if FAILS else 0
