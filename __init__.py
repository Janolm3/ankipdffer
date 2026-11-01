import os
import re
import urllib.parse
import base64
import mimetypes
import tempfile
import traceback
import datetime
import json
import uuid
import shutil
import shlex
import random
import html as html_module
import subprocess
import sys
import threading
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, showWarning, askUser

from .store import (
    DEFAULT_SETTINGS, DEFAULT_FIELD_CONFIG, MACHINE_KEYS, SettingsStore,
    coerce_field_config, coerce_settings,
)
from .translations import LANGUAGES, STRINGS as _EXTRA_STRINGS
from . import macui

try:
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
except ImportError:
    from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineSettings


_STRINGS = {
    "en": {
        "window_title": "Anki → PDF",
        "menu_root": "AnkiPdffer",
        "menu_action": "Open export dialog...",
        "menu_quick_legacy": "Quick Legacy HTML (current deck)",
        "deck_group": "Deck",
        "deck_lbl": "Deck:",
        "subdeck_lbl": "Subdeck:",
        "entire_deck": "(Entire deck)",
        "tab_basic": "⚡ Basic",
        "tab_advanced": "🔧 Advanced",
        "tab_fields": "📋 Fields",
        "tab_settings": "⚙️ Settings",
        "lbl_theme": "Theme:",
        "theme_light": "☀️ Light",
        "theme_dark": "🌙 Dark",
        "theme_pro": "🔵 Pro",
        "lbl_font": "Font:",
        "lbl_size": "Size:",
        "lbl_width": "Width:",
        "width_narrow": "Narrow (520px)",
        "width_medium": "Medium (680px)",
        "width_wide": "Wide (860px)",
        "width_full": "Full",
        "width_custom": "Custom",
        "lbl_layout": "Layout:",
        "layout_standard": "Standard",
        "layout_compact": "Compact",
        "lbl_source": "Source:",
        "source_fields": "Fields",
        "source_cards": "Cards (Cloze/Occlusion)",
        "cb_title": "Title",
        "cb_numbers": "Numbers",
        "cb_zebra": "Zebra",
        "lbl_page": "Page:",
        "lbl_margins": "Margins:",
        "lbl_top_margin": "Top margin:",
        "lbl_padding": "Padding:",
        "lbl_gap": "Min gap:",
        "lbl_lineheight": "Line height:",
        "lbl_maximg": "Max img:",
        "cb_strip_html": "Strip Anki formatting",
        "lbl_card_style": "Card style:",
        "style_rounded": "Rounded + shadow",
        "style_sharp": "Sharp edges",
        "style_separator": "Separator",
        "style_double": "Double border",
        "style_none": "No border",
        "fields_hint": "Assign each field to a section. <b>⋯</b> = more options.",
        "sec_front": "Front",
        "sec_back": "Back",
        "sec_extra": "Extra",
        "field_lbl_label": "Label",
        "field_lbl_bg": "Bg:",
        "field_lbl_color": "Color:",
        "field_lbl_align": "Align:",
        "field_bg": ["Auto", "White", "Light gray", "Blue tint", "Yellow tint",
                     "Green tint", "Red tint", "Lavender"],
        "field_color": ["Default", "Gray", "Red", "Blue", "Green", "Orange", "Purple"],
        "field_align": ["Left", "Center", "Justify", "Right"],
        "grp_settings": "Settings",
        "btn_save_settings": "Save settings",
        "btn_load_settings": "Load settings",
        "btn_reset_settings": "Reset to defaults",
        "grp_language": "Language",
        "lang_hint": "Restart Anki to apply.",
        "grp_debug": "Debug",
        "cb_debug": "Debug mode",
        "btn_logs": "Logs",
        "cb_grid": "Grid",
        "btn_legacy": "Legacy HTML",
        "btn_preview": "Preview PDF",
        "btn_export": "Export PDF",
        "generating": "Generating…",
        "printing": "Printing…",
        "busy_legacy": "Generating Legacy HTML...",
        "busy_preview": "Generating PDF preview...",
        "busy_pdf_html": "Preparing PDF...",
        "busy_pdf_render": "Rendering PDF...",
        "busy_opening": "Opening result...",
        "busy_hint": "Keep this window open while Anki prepares the file.",
        "dlg_save_pdf": "Save PDF",
        "pdf_filter": "PDF (*.pdf)",
        "msg_settings_saved": "Saved: {}",
        "msg_settings_err": "Save error: {}",
        "msg_no_settings": "No saved settings found.",
        "msg_settings_loaded": "Settings loaded.",
        "msg_settings_load_err": "Load error: {}",
        "msg_settings_reset": "Settings reset to defaults.",
        "msg_error": "Error.",
        "msg_pdf_saved": "PDF saved to:\n{}",
        "msg_log_saved": "Saved: {}",
        "logs_title": "Logs",
        "btn_copy": "Copy",
        "btn_save": "Save",
        "btn_close": "Close",
        "no_logs": "(None)",
        "lbx_close_title": "Close (Esc)",
        "rendered_front": "Front",
        "rendered_back": "Back",
        "page_break_lbl": "✂ Page break",
        "cb_high_contrast": "High contrast (override card styles)",
        "pdf_footer_generated": "Generated with {tool} v{version}",
        "pdf_top_tool_notice": "{tool} · {url}",
    },
    "pl": {
        "window_title": "Anki → PDF",
        "menu_root": "AnkiPdffer",
        "menu_action": "Otwórz okno eksportu...",
        "menu_quick_legacy": "Szybki Legacy HTML (bieżący deck)",
        "deck_group": "Deck",
        "deck_lbl": "Deck:",
        "subdeck_lbl": "Subdeck:",
        "entire_deck": "(Cały deck)",
        "tab_basic": "⚡ Podstawowe",
        "tab_advanced": "🔧 Zaawansowane",
        "tab_fields": "📋 Pola",
        "tab_settings": "⚙️ Ustawienia",
        "lbl_theme": "Motyw:",
        "theme_light": "☀️ Jasny",
        "theme_dark": "🌙 Ciemny",
        "theme_pro": "🔵 Pro",
        "lbl_font": "Czcionka:",
        "lbl_size": "Rozmiar:",
        "lbl_width": "Szerokość:",
        "width_narrow": "Wąska (520px)",
        "width_medium": "Średnia (680px)",
        "width_wide": "Szeroka (860px)",
        "width_full": "Pełna",
        "width_custom": "Własna",
        "lbl_layout": "Układ:",
        "layout_standard": "Standardowy",
        "layout_compact": "Kompaktowy",
        "lbl_source": "Źródło:",
        "source_fields": "Pola",
        "source_cards": "Karty (Cloze/Occlusion)",
        "cb_title": "Tytuł",
        "cb_numbers": "Numery",
        "cb_zebra": "Zebra",
        "lbl_page": "Strona:",
        "lbl_margins": "Marginesy:",
        "lbl_top_margin": "Góra/dół:",
        "lbl_padding": "Padding:",
        "lbl_gap": "Min gap:",
        "lbl_lineheight": "Interlinia:",
        "lbl_maximg": "Maks. img:",
        "cb_strip_html": "Wyczyść formatowanie Anki",
        "lbl_card_style": "Styl karty:",
        "style_rounded": "Zaokrąglona + cień",
        "style_sharp": "Ostre krawędzie",
        "style_separator": "Separator",
        "style_double": "Podwójna ramka",
        "style_none": "Bez ramki",
        "fields_hint": "Przypisz każde pole do sekcji. <b>⋯</b> = dodatkowe opcje.",
        "sec_front": "Pytanie (góra)",
        "sec_back": "Odpowiedź (dół)",
        "sec_extra": "Dodatkowe",
        "field_lbl_label": "Etykieta",
        "field_lbl_bg": "Tło:",
        "field_lbl_color": "Kolor:",
        "field_lbl_align": "Wyrówn.:",
        "field_bg": ["Auto", "Białe", "Jasnoszare", "Błękitne",
                     "Żółtawe", "Zielonawe", "Czerwonawe", "Lawendowe"],
        "field_color": ["Domyślny", "Szary", "Czerwony", "Niebieski",
                        "Zielony", "Pomarańczowy", "Fioletowy"],
        "field_align": ["Lewo", "Środek", "Justuj", "Prawo"],
        "grp_settings": "Zarządzanie ustawieniami",
        "btn_save_settings": "Zapisz ustawienia",
        "btn_load_settings": "Wczytaj ustawienia",
        "btn_reset_settings": "Resetuj do domyślnych",
        "grp_language": "Język / Language",
        "lang_hint": "Wymagany restart Anki.",
        "grp_debug": "Debugowanie",
        "cb_debug": "Tryb debugowania",
        "btn_logs": "Logi",
        "cb_grid": "Siatka",
        "btn_legacy": "Legacy HTML",
        "btn_preview": "Podgląd PDF",
        "btn_export": "Eksportuj PDF",
        "generating": "Generowanie…",
        "printing": "Drukowanie…",
        "busy_legacy": "Generowanie Legacy HTML...",
        "busy_preview": "Generowanie podglądu PDF...",
        "busy_pdf_html": "Przygotowywanie PDF...",
        "busy_pdf_render": "Renderowanie PDF...",
        "busy_opening": "Otwieranie wyniku...",
        "busy_hint": "Zostaw to okno otwarte, Anki przygotowuje plik.",
        "dlg_save_pdf": "Zapisz PDF",
        "pdf_filter": "PDF (*.pdf)",
        "msg_settings_saved": "Zapisano: {}",
        "msg_settings_err": "Błąd zapisu ustawień: {}",
        "msg_no_settings": "Brak zapisanych ustawień.",
        "msg_settings_loaded": "Wczytano ustawienia.",
        "msg_settings_load_err": "Błąd wczytywania ustawień: {}",
        "msg_settings_reset": "Przywrócono ustawienia domyślne.",
        "msg_error": "Błąd.",
        "msg_pdf_saved": "PDF zapisano w:\n{}",
        "msg_log_saved": "Zapisano: {}",
        "logs_title": "Logi",
        "btn_copy": "Kopiuj",
        "btn_save": "Zapisz",
        "btn_close": "Zamknij",
        "no_logs": "(Brak)",
        "lbx_close_title": "Zamknij (Esc)",
        "rendered_front": "Przód",
        "rendered_back": "Tył",
        "page_break_lbl": "✂ Podział strony",
        "cb_high_contrast": "Wysoki kontrast (nadpisz style kart)",
        "pdf_footer_generated": "Wygenerowano przez {tool} v{version}",
        "pdf_top_tool_notice": "{tool} · {url}",
    },
}

for _code, _table in _EXTRA_STRINGS.items():
    _STRINGS.setdefault(_code, {}).update(_table)

_store = SettingsStore(os.path.join(os.path.dirname(__file__), "settings.json"))
_lang = _store.settings.get("language", "en")
if _lang not in _STRINGS:
    _lang = "en"


def _set_language(code):
    global _lang
    _lang = code if code in _STRINGS else "en"


def _t(key):
    return _STRINGS.get(_lang, _STRINGS["en"]).get(key, _STRINGS["en"].get(key, key))


class NoScrollComboBox(QComboBox):
    def wheelEvent(self, e):
        if not self.hasFocus():
            e.ignore()
            return
        super().wheelEvent(e)

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)


class NoScrollSpinBox(QSpinBox):
    def wheelEvent(self, e):
        if not self.hasFocus():
            e.ignore()
            return
        super().wheelEvent(e)

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)


class NoScrollDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, e):
        if not self.hasFocus():
            e.ignore()
            return
        super().wheelEvent(e)

    def focusInEvent(self, e):
        super().focusInEvent(e)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)


class ExportLogger:
    def __init__(self):
        self.entries = []
        self._start = None

    def start(self, label="Export"):
        self._start = datetime.datetime.now()
        self.entries.clear()
        self.log("== {} START ==".format(label))

    def log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.entries.append("[{}] {}".format(ts, msg))

    def error(self, msg, exc=None):
        self.log("ERROR: {}".format(msg))
        if exc:
            self.log(traceback.format_exc())

    def finish(self):
        elapsed = (datetime.datetime.now() - self._start).total_seconds() if self._start else 0
        self.log("== DONE ({:.2f}s) ==".format(elapsed))

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.entries))

    def text(self):
        return "\n".join(self.entries)


logger = ExportLogger()
EXPORT_BUILD = "1.4.1-20261101"
TOOL_NAME = "AnkiPdffer"
TOOL_URL = "https://ankiweb.net/shared/info/1987190048"
TOOL_URL_DISPLAY = "ankiweb.net/shared/info/1987190048"


def _addon_version(default="1.4.1"):
    try:
        manifest_path = os.path.join(os.path.dirname(__file__), "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        return manifest.get("human_version", default)
    except Exception:
        return default


# Runs inside the isolated WeasyPrint process (see _export_pdf_via_weasyprint). Cards start as
# unbreakable; after each render, a card that was pushed to the next page while leaving more than
# `gap_ratio` of the previous page empty is allowed to continue across the break (only between
# fields, never inside one), and the document is rendered again. Cards that WeasyPrint had to split
# anyway (taller than a page) are marked too, so they flow instead of being clipped.
_LAYOUT_PASS_SCRIPT = """
    def write_optimised(HTML, html_path, pdf_path, layout_json):
        import re as _re
        try:
            layout = json.loads(layout_json or '{}')
        except Exception:
            layout = {}
        ratio = float(layout.get('gap_ratio') or 0)
        min_card = float(layout.get('min_split') or 0)
        with open(html_path, encoding='utf-8') as fh:
            source = fh.read()
        base = os.path.dirname(html_path)

        def render(markup):
            return HTML(string=markup, base_url=base).render()

        def pages_of(doc):
            out = []
            for page in doc.pages:
                pb = page._page_box
                top = pb.content_box_y()
                cards = []
                stack = [pb]
                while stack:
                    b = stack.pop()
                    el = getattr(b, 'element', None)
                    uid = el.get('data-u') if el is not None and hasattr(el, 'get') else None
                    if uid is not None:
                        # where the card's own content ends inside this fragment (text, images):
                        # a split fragment's frame always runs to the bottom of the page
                        inner, leaves = b.position_y, list(getattr(b, 'children', None) or [])
                        while leaves:
                            leaf = leaves.pop()
                            kids = getattr(leaf, 'children', None)
                            if kids:
                                leaves.extend(kids)
                            else:
                                inner = max(inner, leaf.position_y + leaf.margin_height())
                        cards.append((b.position_y, b.position_y + b.margin_height(), uid,
                                      el.get('data-keep') == '1', inner))
                        continue
                    stack.extend(getattr(b, 'children', None) or [])
                cards.sort()
                out.append((top, top + pb.height, cards))
            return out

        def stats(pages):
            where = {}
            for i, (_, _, cards) in enumerate(pages):
                for c in cards:
                    where.setdefault(c[2], []).append(i)
            split = {u for u, p in where.items() if len(set(p)) > 1}
            gaps = [(bottom - max(c[1] for c in cards)) / (bottom - top)
                    for top, bottom, cards in pages[:-1] if cards]
            return split, gaps

        def wasted_frames(pages, split, motive):
            # A split card's first part is framed down to the page end. Keep the split only if
            # that empty frame is clearly smaller than the gap it was meant to fill.
            seen, bad = set(), set()
            for top, bottom, cards in pages:
                for c in cards:
                    if c[2] in split and c[2] in motive and c[2] not in seen:
                        seen.add(c[2])
                        if (c[1] - c[4]) / (bottom - top) > motive[c[2]] - ratio:
                            bad.add(c[2])
            return bad

        def with_marks(marked):
            def sub(m):
                cls = m.group(2)
                if m.group(5) in marked and 'split-ok' not in cls:
                    cls += ' split-ok'
                return m.group(1) + cls + m.group(3) + m.group(4)
            return _re.sub(r'(<div class=")(card[^"]*)(")([^>]*?\\bdata-u="(\\d+)")', sub, source)

        doc = render(source)
        marked, blocked, motive, renders = set(), set(), {}, 1
        while ratio > 0 and renders < int(layout.get('max_renders') or 3):
            pages = pages_of(doc)
            split, _ = stats(pages)
            bad = wasted_frames(pages, split, motive) & marked
            new = set()
            for i in range(len(pages) - 1):
                top, bottom, cards = pages[i]
                if not cards or bottom - max(c[1] for c in cards) <= ratio * (bottom - top):
                    continue
                ntop, _, ncards = pages[i + 1]
                here = {c[2] for c in cards}
                first = next((c for c in ncards if c[2] not in here), None)
                if not first or first[3] or first[0] - ntop >= 3 or first[2] in marked | blocked:
                    continue
                # short cards are never cut: moving them whole wastes at most their own height
                if first[1] - first[0] > min_card * (bottom - top) or first[2] in split:
                    new.add(first[2])
                    motive[first[2]] = (bottom - max(c[1] for c in cards)) / (bottom - top)
            if not new and not bad:
                break
            blocked |= bad
            marked = (marked | new) - blocked
            doc = render(with_marks(marked))
            renders += 1
        split, gaps = stats(pages_of(doc))
        print('Layout: {} pages, {} of {} cards continue on the next page, {:.0%} average empty, '
              '{} render pass(es), gap limit {:.0%}'.format(
                  len(doc.pages), len(split), source.count(' data-u="'),
                  (sum(gaps) / len(gaps)) if gaps else 0, renders, ratio), flush=True)
        doc.write_pdf(pdf_path)
"""


class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)

    def javaScriptConsoleMessage(self, level, msg, line, src):
        logger.log("JS [{}] L{}: {}".format(level, line, msg))


class FieldConfigWidget(QWidget):
    """One row of the Fields table. `changed` fires on any edit so settings autosave.

    Wide mode keeps every control on one line, in columns that line up with the table's
    column header. Compact mode (narrow windows) moves size / style / label to a second line.
    """

    changed = pyqtSignal()
    MARGINS = (12, 7, 8, 7)
    SPACING = 8
    NAME_MIN = 96

    def __init__(self, field_name, is_front=False, nt_id=0, nt_name="", config=None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("last", False)
        self.field_name = field_name
        self.nt_id = nt_id
        self.nt_name = nt_name
        self._compact = False
        root = QVBoxLayout(self)
        root.setContentsMargins(*self.MARGINS)
        root.setSpacing(6)

        line1 = QHBoxLayout()
        line1.setSpacing(self.SPACING)
        self.export_cb = QCheckBox()
        self.export_cb.setChecked(True)
        self.export_cb.setToolTip(_t("col_export"))
        line1.addWidget(self.export_cb)
        self.name_label = macui.ElidedLabel(field_name)
        self.name_label.setMinimumWidth(self.NAME_MIN)
        line1.addWidget(self.name_label, 1)
        self.section_combo = NoScrollComboBox()
        self.section_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.section_combo.addItems([_t("sec_front"), _t("sec_back"), _t("sec_extra")])
        self.section_combo.setCurrentIndex(0 if is_front else 1)
        line1.addWidget(self.section_combo)

        self.size_radio = macui.SegmentedControl(["S", "M", "L", "XL"], default=(2 if is_front else 1))
        self.size_radio.setToolTip(_t("col_size"))
        self.format_strip = macui.SegmentedControl(["B", "I", "U"], exclusive=False)
        self.format_strip.setToolTip(_t("col_style"))
        self.bold_cb, self.italic_cb, self.underline_cb = self.format_strip.buttons
        for btn, attr in ((self.bold_cb, "setBold"), (self.italic_cb, "setItalic"),
                          (self.underline_cb, "setUnderline")):
            f = btn.font()
            getattr(f, attr)(True)
            btn.setFont(f)
        self.bold_cb.setChecked(is_front)
        # the label check box sits centred in a fixed column under its header
        self.label_cb = QCheckBox()
        self.label_cb.setChecked(not is_front)
        self.label_cb.setToolTip(_t("field_lbl_label"))
        self.label_col = QWidget()
        lc = QHBoxLayout(self.label_col)
        lc.setContentsMargins(0, 0, 0, 0)
        lc.addStretch()
        lc.addWidget(self.label_cb)
        lc.addStretch()
        self.label_col.setFixedWidth(self.label_col_width())
        self._details = (self.size_radio, self.format_strip, self.label_col)
        self._slot = QHBoxLayout()
        self._slot.setSpacing(self.SPACING)
        for w in self._details:
            self._slot.addWidget(w)
        line1.addLayout(self._slot)

        self.adv_btn = QPushButton("\u22ef")
        self.adv_btn.setObjectName("Plain")
        self.adv_btn.setCheckable(True)
        self.adv_btn.setToolTip(_t("fields_hint"))
        self.adv_btn.setFixedSize(24, 22)
        self.adv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.adv_btn.clicked.connect(self._toggle)
        line1.addWidget(self.adv_btn)
        root.addLayout(line1)

        self.line2 = QWidget()
        self._line2 = QHBoxLayout(self.line2)
        self._line2.setContentsMargins(self.indent(), 0, 0, 0)
        self._line2.setSpacing(self.SPACING)
        self._line2.addStretch()
        self.line2.setVisible(False)
        root.addWidget(self.line2)

        self.adv_panel = QWidget()
        self.adv_panel.setVisible(False)
        ap = QHBoxLayout(self.adv_panel)
        ap.setContentsMargins(self.indent(), 2, 0, 2)
        ap.setSpacing(8)
        self.bg_combo = NoScrollComboBox()
        self.color_combo = NoScrollComboBox()
        self.align_combo = NoScrollComboBox()
        for label_key, combo, items_key in (("field_lbl_bg", self.bg_combo, "field_bg"),
                                            ("field_lbl_color", self.color_combo, "field_color"),
                                            ("field_lbl_align", self.align_combo, "field_align")):
            lbl = QLabel(_t(label_key))
            lbl.setObjectName("Secondary")
            ap.addWidget(lbl)
            combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            combo.addItems(_t(items_key))
            ap.addWidget(combo)
            ap.addSpacing(6)
        ap.addStretch()
        root.addWidget(self.adv_panel)

        if config:
            self.set_config(config)
        self._sync_enabled()
        self._wire_changes()

    # ------------------------------------------------------------ geometry
    def finalize_columns(self):
        """Fix the column widths. Call once the row sits in the dialog: only then does the
        stylesheet apply, and the native (unstyled) sizes are far wider."""
        self.ensurePolished()
        # the macOS style pads combo boxes / buttons with invisible layout margins; the
        # column header has none, so lay rows out by the visible widget rects instead
        for w in self.findChildren(QWidget):
            w.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect, True)
        for seg in (self.size_radio, self.format_strip):
            seg.layout().invalidate()
            seg.setFixedWidth(seg.sizeHint().width())
        self.section_combo.setFixedWidth(max(150, self.section_combo.sizeHint().width()))
        self.adv_btn.setFixedSize(24, 22)  # after polish: the stylesheet's min-width would win otherwise
        pal = macui.palette(_is_dark_mode())
        for combo in (self.section_combo, self.bg_combo, self.color_combo, self.align_combo):
            macui.round_popup(combo, pal)

    @staticmethod
    def label_col_width():
        metrics = QFontMetrics(QApplication.font())
        return max(28, metrics.horizontalAdvance(_t("field_lbl_label").upper()) + 6)

    def indent(self):
        """Left offset of the field name (and of everything shown below it)."""
        return self.export_cb.sizeHint().width() + self.SPACING

    def column_widths(self):
        """Widths of the fixed columns, for the table header."""
        return dict(lead=self.indent(), section=self.section_combo.maximumWidth(),
                    size=self.size_radio.maximumWidth(), style=self.format_strip.maximumWidth(),
                    label=self.label_col_width(), trail=self.adv_btn.maximumWidth())

    def wide_width(self):
        """Smallest row width that still fits everything on one line."""
        c = self.column_widths()
        left, _, right, _ = self.MARGINS
        return (left + right + c["lead"] + self.NAME_MIN + c["section"] + c["size"] + c["style"]
                + c["label"] + c["trail"] + 5 * self.SPACING)

    def set_compact(self, compact):
        if compact == self._compact:
            return
        self._compact = compact
        src, dst = (self._slot, self._line2) if compact else (self._line2, self._slot)
        for i, w in enumerate(self._details):
            src.removeWidget(w)
            dst.insertWidget(i, w)
        # with no column header above it the check box needs its own caption
        self.label_cb.setText(_t("field_lbl_label") if compact else "")
        if compact:
            self.label_col.setMinimumWidth(0)
            self.label_col.setMaximumWidth(16777215)
        else:
            self.label_col.setFixedWidth(self.label_col_width())
        self.line2.setVisible(compact)

    # ------------------------------------------------------------- state
    def _wire_changes(self):
        emit = lambda *_: self.changed.emit()
        for cb in (self.export_cb, self.bold_cb, self.label_cb, self.italic_cb, self.underline_cb):
            cb.toggled.connect(emit)
        for combo in (self.section_combo, self.bg_combo, self.color_combo, self.align_combo):
            combo.currentIndexChanged.connect(emit)
        self.size_radio.group.idToggled.connect(emit)
        self.export_cb.toggled.connect(self._sync_enabled)

    def _sync_enabled(self, *_):
        """A field that is not exported keeps its settings but greys them out."""
        on = self.export_cb.isChecked()
        for w in (self.name_label, self.section_combo, self.size_radio, self.format_strip,
                  self.label_col, self.adv_btn, self.adv_panel):
            w.setEnabled(on)

    def _toggle(self):
        self.adv_panel.setVisible(self.adv_btn.isChecked())

    def get_config(self):
        return dict(
            export=self.export_cb.isChecked(),
            section=self.section_combo.currentIndex(),
            size=self.size_radio.currentIndex(),
            bold=self.bold_cb.isChecked(),
            label=self.label_cb.isChecked(),
            bg=self.bg_combo.currentIndex(),
            color=self.color_combo.currentIndex(),
            align=self.align_combo.currentIndex(),
            italic=self.italic_cb.isChecked(),
            underline=self.underline_cb.isChecked(),
        )

    def set_config(self, cfg):
        cfg = coerce_field_config(cfg)
        self.export_cb.setChecked(cfg["export"])
        self.section_combo.setCurrentIndex(cfg["section"])
        self.size_radio.setCurrentIndex(cfg["size"])
        self.bold_cb.setChecked(cfg["bold"])
        self.label_cb.setChecked(cfg["label"])
        self.bg_combo.setCurrentIndex(cfg["bg"])
        self.color_combo.setCurrentIndex(cfg["color"])
        self.align_combo.setCurrentIndex(cfg["align"])
        self.italic_cb.setChecked(cfg["italic"])
        self.underline_cb.setChecked(cfg["underline"])


class FieldTableHeader(QWidget):
    """Column captions for one note type's Fields table, aligned with its rows."""

    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.setObjectName("TableColumns")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        c = row.column_widths()
        ly = QHBoxLayout(self)
        left, _, right, _ = FieldConfigWidget.MARGINS
        ly.setContentsMargins(left, 6, right, 5)
        ly.setSpacing(FieldConfigWidget.SPACING)
        # QBoxLayout adds no spacing next to spacer items, so the spacers carry it themselves
        ly.addSpacing(c["lead"])

        def caption(key, width=None, align=Qt.AlignmentFlag.AlignLeft):
            lbl = QLabel(_t(key).upper())
            lbl.setObjectName("ColumnHeader")
            lbl.setAlignment(align | Qt.AlignmentFlag.AlignVCenter)
            if width:
                lbl.setFixedWidth(width)
            return lbl

        ly.addWidget(caption("col_field"), 1)
        ly.addWidget(caption("col_section", c["section"]))
        center = Qt.AlignmentFlag.AlignHCenter
        self.details = [caption("col_size", c["size"], center), caption("col_style", c["style"], center),
                        caption("field_lbl_label", c["label"], center)]
        for lbl in self.details:
            ly.addWidget(lbl)
        ly.addSpacing(c["trail"] + FieldConfigWidget.SPACING)

    def set_compact(self, compact):
        for lbl in self.details:
            lbl.setVisible(not compact)


PAGE_SIZES = {"A4": (210, 297), "Letter": (216, 279), "A3": (297, 420), "A5": (148, 210)}

CARD_WIDTH_PRESETS = [
    ("Wąska — 520px", 520),
    ("Średnia — 680px", 680),
    ("Szeroka — 860px", 860),
    ("Pełna", 0),
    ("Własna…", -1),
]

FONT_OPTIONS = [
    ("System", "'SF Pro Text','SF Pro Display','System Font',-apple-system,BlinkMacSystemFont,'Inter','Helvetica Neue',Helvetica,Arial,sans-serif"),
    ("Inter", "'Inter','SF Pro Text',-apple-system,BlinkMacSystemFont,'Helvetica Neue',sans-serif"),
    ("Helvetica", "'Helvetica Neue',Helvetica,Arial,sans-serif"),
    ("Arial", "Arial,'Helvetica Neue',Helvetica,sans-serif"),
    ("Georgia", "Georgia,'Times New Roman',Times,serif"),
    ("Times New Roman", "'Times New Roman',Times,Georgia,serif"),
    ("Verdana", "Verdana,Tahoma,Geneva,sans-serif"),
    ("Tahoma", "Tahoma,Verdana,Geneva,sans-serif"),
    ("Trebuchet MS", "'Trebuchet MS','Lucida Grande','Lucida Sans',sans-serif"),
    ("Palatino", "'Palatino Linotype',Palatino,'Book Antiqua',serif"),
    ("Fira Code", "'Fira Code','Courier New',monospace"),
    ("Courier New", "'Courier New',Courier,monospace"),
]

GENERIC_FONT_FAMILIES = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
    "ui-serif", "ui-sans-serif", "ui-monospace", "ui-rounded",
    "emoji", "math", "fangsong", "blinkmacsystemfont",
}


def _split_font_stack(stack):
    families = []
    buf = []
    quote = None
    escaped = False
    for ch in stack or "":
        if escaped:
            buf.append(ch)
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if quote:
            if ch == quote:
                quote = None
            else:
                buf.append(ch)
            continue
        if ch in ("'", '"'):
            quote = ch
            continue
        if ch == ",":
            family = "".join(buf).strip()
            if family:
                families.append(family)
            buf = []
            continue
        buf.append(ch)
    family = "".join(buf).strip()
    if family:
        families.append(family)
    return families


def _real_font_candidates(stack):
    out = []
    seen = set()
    for family in _split_font_stack(stack):
        normalized = family.lower()
        if normalized in GENERIC_FONT_FAMILIES or family.startswith("-"):
            continue
        if normalized not in seen:
            seen.add(normalized)
            out.append(family)
    return out


THEME_PRESETS = [
    dict(
        body="#ffffff",
        card="#ffffff",
        brd="#e2e8f0",
        txt="#0f172a",
        mut="#64748b",
        acc="#0f172a",
        div="#e2e8f0",
        alt="#f8fafc",
        shadow="0 10px 26px rgba(15,23,42,.06), 0 2px 8px rgba(15,23,42,.04)",
        accent_brd="#cbd5e1",
    ),
    dict(
        body="#111111",
        card="#1a1a1a",
        brd="#2a2a2a",
        txt="#e5e5e5",
        mut="#666666",
        acc="#ffffff",
        div="#2a2a2a",
        alt="#151515",
        shadow="0 16px 30px rgba(0,0,0,.35), 0 4px 12px rgba(0,0,0,.24)",
        accent_brd="#3f3f46",
    ),
    dict(
        body="#f3f7ff",
        card="#ffffff",
        brd="#d6e4ff",
        txt="#13233d",
        mut="#5b6b86",
        acc="#1d4ed8",
        div="#dbe6ff",
        alt="#eef4ff",
        shadow="0 16px 34px rgba(37,99,235,.10), 0 4px 10px rgba(15,23,42,.05)",
        accent_brd="#93c5fd",
    ),
]

THEME_CLASS_NAMES = ["theme-light", "theme-dark", "theme-pro"]
THEME_DISPLAY_NAMES = ["Light", "Dark", "Pro"]


def _theme_tokens(index):
    if 0 <= index < len(THEME_PRESETS):
        return THEME_PRESETS[index]
    return THEME_PRESETS[0]


def _is_dark_mode():
    try:
        from aqt import mw
        if mw and mw.pm:
            return bool(mw.pm.night_mode())
    except Exception:
        pass
    try:
        from aqt.theme import theme_manager
        return bool(theme_manager.night_mode)
    except Exception:
        pass
    try:
        from aqt import theme_manager
        return bool(theme_manager.night_mode)
    except Exception:
        pass
    return False


_SEARCH_ESCAPE_RE = re.compile(r'([\\"*_])')
_FRONT_FIELD_HINTS = ("pytanie", "question", "front", "przod", "zagadnienie", "text", "tekst",
                      "header", "image")


def _deck_query(deck_name):
    """Anki search for a deck (and its subdecks) with the special characters escaped."""
    return '"deck:{}"'.format(_SEARCH_ESCAPE_RE.sub(r'\\\1', deck_name or ""))


def _is_front_field(name):
    low = (name or "").lower()
    return any(k in low for k in _FRONT_FIELD_HINTS)


def _auto_field_config(name):
    front = _is_front_field(name)
    return coerce_field_config({
        "section": 0 if front else 1, "size": 2 if front else 1,
        "bold": front, "label": not front,
    })


def _notetype_is_io(nt):
    try:
        if nt.get("originalStockKind") == 6:
            return True
    except AttributeError:
        pass
    return "image occlusion" in (nt.get("name") or "").lower()


_MEDIA_TAG_RE = re.compile(r'\[sound:[^\]]*\]|\[anki:play:[^\]]*\]|\[\[type:[^\]]*\]\]')
_ANSWER_HR_RE = re.compile(r'<hr\s+id=["\']?answer["\']?\s*/?>', re.IGNORECASE)
_CLOZE_INNER_RE = re.compile(r'\{\{c(\d+)::((?:(?!\{\{c\d+::).)*?)\}\}', re.DOTALL)
_IO_SHAPE_RE = re.compile(r'\{\{c(\d+)::image-occlusion:(\w+)((?::[^:{}]*)*)\}\}')
_IMG_TAG_RE = re.compile(r'<img\b[^>]*>', re.IGNORECASE)
_POINT_RE = re.compile(r'^-?\d*\.?\d+,-?\d*\.?\d+$')


def _cloze_render(text, reveal):
    """Resolve {{cN::answer::hint}} markers (nested ones too, innermost first).

    reveal=True  -> answers shown, highlighted
    reveal=False -> answers replaced by [hint] / [...]
    """
    def sub(m):
        answer, sep, hint = m.group(2).partition("::")
        if reveal:
            return '<span class="cz-a">{}</span>'.format(answer)
        return '<span class="cz-h">[{}]</span>'.format(hint if sep and hint else "...")

    previous = None
    while previous != text:
        previous = text
        text = _CLOZE_INNER_RE.sub(sub, text)
    return text


def _parse_io(fields_by_name, nt):
    """Parse an Image Occlusion note into shapes + image + remaining fields.

    Anki >= 23.10 stores masks as {{cN::image-occlusion:rect:left=..:top=..}} in the
    Occlusion field and draws them with JavaScript, so a static export has to draw
    them itself. Returns None when the note is not an (intact) Image Occlusion note.
    """
    flds = sorted(nt["flds"], key=lambda f: f["ord"])
    occ = next((f["name"] for f in flds
                if "image-occlusion:" in fields_by_name.get(f["name"], "")), None)
    if occ is None:
        return None
    shapes = []
    for m in _IO_SHAPE_RE.finditer(fields_by_name[occ]):
        params = {}
        for part in m.group(3).split(":"):
            key, eq, val = part.partition("=")
            if eq:
                params[key] = val

        def num(key):
            try:
                return float(params.get(key, "0"))
            except ValueError:
                return 0.0

        shapes.append({
            "ord": int(m.group(1)), "kind": m.group(2),
            "left": num("left"), "top": num("top"),
            "width": num("width"), "height": num("height"),
            "points": params.get("points", ""), "oi": params.get("oi") == "1",
        })
    image, rest = "", []
    for f in flds:
        if f["name"] == occ:
            continue
        val = fields_by_name.get(f["name"], "")
        if not val.strip():
            continue
        found = _IMG_TAG_RE.search(val) if not image else None
        if found:
            image = found.group(0)
        else:
            rest.append((f["name"], val))
    if not image or not shapes:
        return None
    return {"shapes": shapes, "image": image, "rest": rest}


def _io_polygon_points(shape):
    pts = [p for p in shape["points"].split() if _POINT_RE.match(p)]
    return pts


def _io_overlay(shapes, css_class, numbered=False):
    """Absolutely positioned shapes (coordinates are fractions of the image size)."""
    out = []
    for sh in shapes:
        if sh["kind"] == "polygon":
            pts = _io_polygon_points(sh)
            if len(pts) < 3:
                continue
            out.append('<svg class="io-poly {}" viewBox="0 0 1 1" preserveAspectRatio="none">'
                       '<polygon points="{}"/></svg>'.format(css_class, " ".join(pts)))
            xs = [float(p.split(",")[0]) for p in pts]
            ys = [float(p.split(",")[1]) for p in pts]
            left, top = min(xs), min(ys)
        else:
            shape_cls = " io-e" if sh["kind"] == "ellipse" else ""
            out.append('<div class="{}{}" style="left:{:.3f}%;top:{:.3f}%;width:{:.3f}%;height:{:.3f}%"></div>'
                       .format(css_class, shape_cls, sh["left"] * 100, sh["top"] * 100,
                               sh["width"] * 100, sh["height"] * 100))
            left, top = sh["left"], sh["top"]
        if numbered:
            out.append('<span class="io-n" style="left:{:.3f}%;top:{:.3f}%">{}</span>'
                       .format(left * 100, top * 100, sh["ord"]))
    return "".join(out)


def _io_figure(image_html, masks=(), outlines=()):
    """<img> with masks drawn over it (masks hide, outlines only show where they were)."""
    return '<div class="io-wrap">{}{}{}</div>'.format(
        image_html, _io_overlay(masks, "io-m"), _io_overlay(outlines, "io-o", numbered=True))


class PDFExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_t("window_title"))
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.page = None
        self.temp_html_path = None
        self.temp_fallback_path = None
        self.field_widgets = []
        self._nt_headers = []
        self._all_decks = []
        self._loading = True  # suppress autosave while the UI is being built / restored
        self._col_ref = mw.col if mw else None

        self.setObjectName("PdfferWindow")
        self._dark = _is_dark_mode()
        self._pal = macui.palette(self._dark)
        self.setStyleSheet(macui.stylesheet(self._dark))

        self._busy_timer = QTimer(self)
        self._busy_timer.timeout.connect(self._animate_busy)
        self._busy_val = 0
        self._base_busy_message = ""

        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            self.resize(max(780, min(int(sg.width() * 0.6), 900)),
                        max(580, min(int(sg.height() * 0.7), 660)))
        else:
            self.resize(820, 660)
        self._active_export_theme_index = None
        self._busy_depth = 0
        self._font_debug_logged_modes = set()
        self._pdf_ready_logged = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_toolbar())

        self.tab_box = macui.TabBox()
        self.tab_box.add_page(_t("tab_content"), self._scroll_page(self._build_content_tab()))
        self.tab_box.add_page(_t("tab_appearance"), self._scroll_page(self._build_appearance_tab()))
        self.tab_box.add_page(_t("tab_page"), self._scroll_page(self._build_page_tab()))
        self.tab_box.add_page(macui.plain(_t("tab_fields")), self._build_fields_tab())
        self.tab_box.add_page(macui.plain(_t("tab_settings")), self._scroll_page(self._build_settings_tab()))
        self.tab_box.finish()
        self.tabs = self.tab_box.tabs
        self.stack = self.tab_box.stack
        self._engine_report = None
        self.stack.currentChanged.connect(
            lambda i: i == self.stack.count() - 1 and self._engine_report is None and self._check_engine())
        body = QVBoxLayout()
        body.setContentsMargins(20, 14, 20, 18)
        self.tab_box.setMinimumHeight(300)
        body.addWidget(self.tab_box, 1)
        root.addLayout(body, 1)
        root.addWidget(self._build_footer())
        self._create_busy_overlay()
        self._install_shortcuts()
        for combo in self.findChildren(QComboBox):
            macui.round_popup(combo, self._pal)
        macui.round_popup(self.field_preset_menu, self._pal)

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._flush_save)
        self._apply_settings(_store.settings)
        self._refresh_presets()
        self._populate_decks()
        self.deck_combo.currentIndexChanged.connect(self._on_deck_changed)
        self.subdeck_combo.currentIndexChanged.connect(self._on_subdeck_changed)
        self._connect_autosave()
        geo = _store.get_geometry()
        if geo:
            self.restoreGeometry(geo)
        self._loading = False

    # ------------------------------------------------------------- layout
    @staticmethod
    def _form_page():
        """A centred, right-aligned-label form (the classic Mac preferences layout)."""
        page = QWidget()
        page.setObjectName("Page")
        outer = QHBoxLayout(page)
        outer.setContentsMargins(20, 8, 20, 16)
        outer.addStretch(1)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(10)
        outer.addLayout(form)
        outer.addStretch(1)
        return page, form

    @staticmethod
    def _scroll_page(widget):
        area = macui.FitWidthScrollArea()
        area.setObjectName("PageScroll")
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        area.setWidget(widget)
        return area

    @staticmethod
    def _hrow(*items, spacing=8):
        ly = QHBoxLayout()
        ly.setSpacing(spacing)
        for it in items:
            if isinstance(it, int):
                ly.addSpacing(it)
            elif isinstance(it, QWidget):
                ly.addWidget(it)
            else:
                ly.addLayout(it)
        return ly

    @staticmethod
    def _popup(items, min_width=0):
        combo = NoScrollComboBox()
        combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        combo.addItems(items)
        if min_width:
            combo.setMinimumWidth(min_width)
        return combo

    @staticmethod
    def _spin(lo, hi, val, sfx, cls=None):
        sp = (cls or NoScrollSpinBox)()
        sp.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        sp.setRange(lo, hi)
        sp.setValue(val)
        if sfx:
            sp.setSuffix(sfx)
        sp.setFixedWidth(92)
        sp.setAlignment(Qt.AlignmentFlag.AlignRight)
        return sp

    @staticmethod
    def _tip_label(text, tip):
        lbl = macui.form_label(text)
        lbl.setToolTip(tip)
        return lbl

    def _build_toolbar(self):
        bar = QFrame()
        bar.setObjectName("Toolbar")
        ly = QHBoxLayout(bar)
        ly.setContentsMargins(16, 10, 16, 10)
        ly.setSpacing(6)
        deck_lbl = QLabel(_t("deck_lbl"))
        deck_lbl.setObjectName("ToolbarLabel")
        ly.addWidget(deck_lbl)
        self.deck_combo = QComboBox()
        self.deck_combo.setMinimumWidth(160)
        self.deck_combo.setMaximumWidth(300)
        self.deck_combo.setMaxVisibleItems(24)
        self.deck_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.deck_combo.setToolTip(_t("deck_lbl").rstrip(":"))
        ly.addWidget(self.deck_combo, 2)
        chevron = QLabel("\u203a")
        chevron.setObjectName("Chevron")
        ly.addWidget(chevron)
        self.subdeck_combo = QComboBox()
        self.subdeck_combo.setMinimumWidth(160)
        self.subdeck_combo.setMaximumWidth(340)
        self.subdeck_combo.setMaxVisibleItems(24)
        self.subdeck_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.subdeck_combo.setToolTip(_t("subdeck_lbl").rstrip(":"))
        ly.addWidget(self.subdeck_combo, 2)
        ly.addSpacing(14)
        ly.addStretch(1)
        self.filter_edit = QLineEdit()
        self.filter_edit.setObjectName("SearchField")
        self.filter_edit.setPlaceholderText(_t("ph_search"))
        self.filter_edit.setToolTip("{}\n{}".format(_t("ph_filter"), _t("tip_filter")))
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.addAction(macui.glyph_icon("search", self._pal),
                                   QLineEdit.ActionPosition.LeadingPosition)
        self.filter_edit.setMinimumWidth(190)
        self.filter_edit.setMaximumWidth(330)
        self.filter_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ly.addWidget(self.filter_edit, 3)

        self._count_timer = QTimer(self)
        self._count_timer.setSingleShot(True)
        self._count_timer.timeout.connect(self._update_count)
        self.filter_edit.textChanged.connect(lambda *_: self._count_timer.start(350))
        return bar

    def _build_content_tab(self):
        page, form = self._form_page()
        self.render_radio = macui.SegmentedControl(
            [_t("source_fields"), _t("source_cards")], default=0)
        self.render_radio.group.idToggled.connect(self._on_render_radio_changed)
        form.addRow(_t("lbl_source"), self.render_radio)

        self.qa_combo = self._popup([_t("qa_together"), _t("qa_key"), _t("qa_pages")], 250)
        self.qa_combo.setToolTip(_t("tip_qa"))
        form.addRow(self._tip_label(_t("lbl_qa"), _t("tip_qa")), self.qa_combo)
        self.cloze_combo = self._popup([_t("cloze_reveal"), _t("cloze_hide"),
                                        _t("cloze_both"), _t("cloze_native")], 250)
        self.cloze_combo.setToolTip(_t("tip_cloze"))
        form.addRow(self._tip_label(_t("lbl_cloze"), _t("tip_cloze")), self.cloze_combo)
        self.io_combo = self._popup([_t("io_all"), _t("io_each")], 250)
        self.io_combo.setToolTip(_t("tip_io"))
        form.addRow(self._tip_label(_t("lbl_io"), _t("tip_io")), self.io_combo)
        self.order_combo = self._popup([_t("order_deck"), _t("order_created"), _t("order_shuffle")], 250)
        form.addRow(_t("lbl_order"), self.order_combo)
        column = (self.qa_combo, self.cloze_combo, self.io_combo, self.order_combo)
        width = max(c.sizeHint().width() for c in column)
        for c in column:  # one aligned column of pop-ups, wide enough for the longest translation
            c.setFixedWidth(width)

        form.addRow(macui.separator())
        self.show_title_cb = QCheckBox(_t("cb_title"))
        self.show_title_cb.setChecked(True)
        self.card_numbers_cb = QCheckBox(_t("cb_numbers"))
        form.addRow(_t("lbl_show"), self._hrow(self.show_title_cb, 10, self.card_numbers_cb))
        return page

    def _build_appearance_tab(self):
        page, form = self._form_page()
        self.theme_radio = macui.SegmentedControl(
            [_t("theme_light"), _t("theme_dark"), _t("theme_pro")], default=0)
        form.addRow(_t("lbl_theme"), self.theme_radio)

        self.font_combo = self._popup([name for name, _ in FONT_OPTIONS], 160)
        self.fontsize_spin = self._spin(10, 24, 13, " px", QSpinBox)
        size_lbl = QLabel(_t("lbl_size"))
        size_lbl.setObjectName("Secondary")
        form.addRow(_t("lbl_font"), self._hrow(self.font_combo, 6, size_lbl, self.fontsize_spin))

        self.width_radio = macui.SegmentedControl([
            _t("width_narrow"), _t("width_medium"), _t("width_wide"),
            _t("width_full"), _t("width_custom"),
        ], default=1)
        for btn in self.width_radio.buttons:
            full = btn.text()
            short = re.sub(r"\s*\(\s*\d+\s*px\s*\)", "", full)
            if short != full:
                btn.setText(short)
                btn.setToolTip(full)
        self.width_spin = self._spin(300, 3000, 800, " px")
        self.width_spin.setVisible(False)
        self.width_radio.group.idToggled.connect(self._on_width_radio_changed)
        form.addRow(_t("lbl_width"), self._hrow(self.width_radio, self.width_spin))

        self.layout_radio = macui.SegmentedControl(
            [_t("layout_standard"), _t("layout_compact")], default=1)
        form.addRow(_t("lbl_layout"), self.layout_radio)
        self.card_style_combo = self._popup([
            _t("style_rounded"), _t("style_sharp"), _t("style_separator"),
            _t("style_double"), _t("style_none"),
        ], 160)
        form.addRow(_t("lbl_card_style"), self.card_style_combo)

        form.addRow(macui.separator())
        self.zebra_cb = QCheckBox(_t("cb_zebra"))
        self.high_contrast_cb = QCheckBox(_t("cb_high_contrast"))
        self.strip_html_cb = QCheckBox(_t("cb_strip_html"))
        self.grid_cb = QCheckBox(_t("cb_grid_html"))
        form.addRow(_t("lbl_extras"), self.zebra_cb)
        for cb in (self.high_contrast_cb, self.strip_html_cb, self.grid_cb):
            form.addRow("", cb)
        return page

    def _build_page_tab(self):
        page, form = self._form_page()
        self.page_combo = self._popup(["A4", "Letter", "A3", "A5"], 92)
        form.addRow(_t("lbl_page"), self.page_combo)
        self.margin_spin = self._spin(5, 40, 15, " mm")
        form.addRow(_t("lbl_margins"), self.margin_spin)
        self.top_margin_spin = self._spin(0, 40, 15, " mm")
        form.addRow(_t("lbl_top_margin"), self.top_margin_spin)
        form.addRow(macui.separator())
        self.padding_spin = self._spin(2, 50, 12, " px")
        form.addRow(_t("lbl_padding"), self.padding_spin)
        self.gap_spin = self._spin(0, 80, 8, " px")
        form.addRow(_t("lbl_gap"), self.gap_spin)
        self.lh_spin = self._spin(1, 3, 1, "", NoScrollDoubleSpinBox)
        self.lh_spin.setRange(1.0, 2.5)
        self.lh_spin.setSingleStep(0.05)
        self.lh_spin.setValue(1.40)
        form.addRow(_t("lbl_lineheight"), self.lh_spin)
        self.img_h_spin = self._spin(60, 800, 240, " px")
        form.addRow(_t("lbl_maximg"), self.img_h_spin)
        form.addRow(macui.separator())
        self.page_numbers_cb = QCheckBox(_t("cb_page_numbers"))
        form.addRow("", self.page_numbers_cb)
        return page

    FIELDS_MAX_WIDTH = 900

    def _build_fields_tab(self):
        self.fields_tab = QWidget()
        self.fields_tab.setObjectName("Page")
        fl = QVBoxLayout(self.fields_tab)
        fl.setContentsMargins(14, 2, 6, 6)
        fl.setSpacing(8)
        hint = QLabel(_t("fields_hint"))
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        fl.addWidget(hint)
        self.fields_scroll = QScrollArea()
        self.fields_scroll.setObjectName("PageScroll")
        self.fields_scroll.setWidgetResizable(True)
        self.fields_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.fields_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.fields_container = QWidget()
        self.fields_container.setObjectName("Page")
        centre = QHBoxLayout(self.fields_container)
        centre.setContentsMargins(0, 0, 8, 8)
        centre.addStretch(1)
        column = QWidget()
        column.setObjectName("Page")
        column.setMaximumWidth(self.FIELDS_MAX_WIDTH)
        column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.fields_layout = QVBoxLayout(column)
        self.fields_layout.setContentsMargins(0, 0, 0, 0)
        self.fields_layout.setSpacing(6)
        self.fields_layout.addWidget(self._build_notetype_bar())
        self.fields_info = QLabel("")
        self.fields_info.setObjectName("SettingsInfoLabel")
        self.fields_info.setVisible(False)
        self.fields_layout.addWidget(self.fields_info)
        self._fields_info_timer = QTimer(self)
        self._fields_info_timer.setSingleShot(True)
        self._fields_info_timer.timeout.connect(lambda: self.fields_info.setVisible(False))
        self.fields_empty = QLabel(_t("deck_count_none"))
        self.fields_empty.setObjectName("Secondary")
        self.fields_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fields_empty.setContentsMargins(0, 40, 0, 0)
        self.fields_layout.addWidget(self.fields_empty)
        self.fields_layout.addStretch()
        centre.addWidget(column, 100)
        centre.addStretch(1)
        self.fields_scroll.setWidget(self.fields_container)
        self.fields_scroll.viewport().installEventFilter(self)
        fl.addWidget(self.fields_scroll)
        self._fields_compact = None
        return self.fields_tab

    def _build_notetype_bar(self):
        """Note type to edit (pre-selected from the current card / deck) + field presets."""
        bar = QWidget()
        bar.setObjectName("Page")
        ly = QHBoxLayout(bar)
        ly.setContentsMargins(2, 0, 0, 2)
        ly.setSpacing(8)
        lbl = QLabel(_t("lbl_note_type"))
        ly.addWidget(lbl)
        self.nt_combo = NoScrollComboBox()
        self.nt_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.nt_combo.setMinimumWidth(180)
        self.nt_combo.setMaximumWidth(320)
        self.nt_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.nt_combo.activated.connect(self._on_notetype_picked)
        ly.addWidget(self.nt_combo, 2)
        self.nt_source = macui.ElidedLabel("")
        self.nt_source.setObjectName("Secondary")
        self.nt_source.setMinimumWidth(0)
        ly.addWidget(self.nt_source, 1)
        self.field_preset_btn = QPushButton(_t("grp_presets"))
        self.field_preset_btn.setToolTip(_t("tip_field_preset"))
        self.field_preset_menu = QMenu(self.field_preset_btn)
        self.field_preset_menu.aboutToShow.connect(self._fill_field_preset_menu)
        self.field_preset_btn.setMenu(self.field_preset_menu)
        self.field_preset_btn.setProperty("menuButton", True)
        ly.addWidget(self.field_preset_btn)
        self.nt_reset_btn = QPushButton(_t("nt_reset"))
        self.nt_reset_btn.clicked.connect(lambda: self._nt_shown and self._reset_note_type(self._nt_shown["name"]))
        ly.addWidget(self.nt_reset_btn)
        self._nt_selected = None      # id of the note type being edited
        self._nt_pinned = None        # why the type sticks across deck changes: "card", "user" or None
        self._nt_shown = None         # its note type dict
        self._detect_pending = True   # pick the current card's type the next time the list loads
        self._deck_nt_counts = {}
        return bar

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Type.Resize and hasattr(self, "fields_scroll")
                and obj is self.fields_scroll.viewport()):
            self._reflow_fields()
        return super().eventFilter(obj, event)

    def _reflow_fields(self, force=False):
        """Switch the field rows between one-line and two-line layout to fit the window."""
        if not self.field_widgets:
            return
        avail = min(self.fields_scroll.viewport().width() - 8, self.FIELDS_MAX_WIDTH) - 2
        need = max(w.wide_width() for w in self.field_widgets)
        compact = avail < need
        if compact == self._fields_compact and not force:
            return
        self._fields_compact = compact
        for w in self.field_widgets + self._nt_headers:
            if hasattr(w, "set_compact"):
                w.set_compact(compact)

    def _build_settings_tab(self):
        page, form = self._form_page()
        self.preset_combo = self._popup([], 200)
        self.preset_apply_btn = QPushButton(_t("btn_preset_apply"))
        self.preset_apply_btn.clicked.connect(self._apply_preset)
        self.preset_delete_btn = QPushButton(_t("btn_preset_delete"))
        self.preset_delete_btn.clicked.connect(self._delete_preset)
        form.addRow(_t("grp_presets") + ":",
                    self._hrow(self.preset_combo, self.preset_apply_btn, self.preset_delete_btn))
        self.preset_save_btn = QPushButton(_t("btn_preset_save"))
        self.preset_save_btn.clicked.connect(self._save_preset)
        form.addRow("", self._hrow(self.preset_save_btn))

        form.addRow(macui.separator())
        self.lang_combo = NoScrollComboBox()
        self.lang_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for code, native in LANGUAGES.items():
            self.lang_combo.addItem(native, code)
        self.lang_combo.setCurrentIndex(max(0, self.lang_combo.findData(_lang)))
        self.lang_combo.setMinimumWidth(200)
        form.addRow(_t("grp_language") + ":", self.lang_combo)
        self.debug_cb = QCheckBox(_t("cb_debug"))
        self.log_btn = QPushButton(_t("btn_logs"))
        self.log_btn.setVisible(False)
        self.log_btn.clicked.connect(self._show_logs)
        self.debug_cb.toggled.connect(self.log_btn.setVisible)
        form.addRow(_t("grp_debug") + ":", self._hrow(self.debug_cb, 6, self.log_btn))

        form.addRow(macui.separator())
        self.engine_status = QLabel(_t("engine_checking"))
        self.engine_status.setWordWrap(True)
        self.engine_status.setMinimumWidth(300)
        self.engine_status.setMaximumWidth(420)
        form.addRow(_t("grp_engine") + ":", self.engine_status)
        self.engine_check_btn = QPushButton(_t("btn_engine_check"))
        self.engine_check_btn.clicked.connect(lambda: self._check_engine(force=True))
        self.engine_setup_btn = QPushButton(_t("btn_engine_setup"))
        self.engine_setup_btn.clicked.connect(self._open_engine_setup)
        form.addRow("", self._hrow(self.engine_check_btn, self.engine_setup_btn))

        form.addRow(macui.separator())
        self.reset_btn = QPushButton(_t("btn_reset_all"))
        self.reset_btn.setObjectName("Destructive")
        self.reset_btn.clicked.connect(self._reset_settings)
        form.addRow("", self._hrow(self.reset_btn))
        self.settings_info = QLabel("")
        self.settings_info.setObjectName("SettingsInfoLabel")
        self.settings_info.setWordWrap(True)
        self.settings_info.setVisible(False)
        form.addRow("", self.settings_info)

        auto_lbl = QLabel(_t("settings_autosave"))
        auto_lbl.setObjectName("HintLabel")
        auto_lbl.setWordWrap(True)
        auto_lbl.setMinimumWidth(320)
        auto_lbl.setMaximumWidth(380)
        form.addRow("", auto_lbl)
        v_lbl = QLabel("AnkiPdffer {}".format(_addon_version()))
        v_lbl.setObjectName("VersionLabel")
        form.addRow("", v_lbl)
        return page

    def _build_footer(self):
        bar = QFrame()
        bar.setObjectName("Footer")
        ly = QHBoxLayout(bar)
        ly.setContentsMargins(20, 10, 20, 12)
        ly.setSpacing(8)
        self.count_label = QLabel("")
        self.count_label.setObjectName("CountLabel")
        ly.addWidget(self.count_label)

        self.busy_wrap = QWidget()
        busy_ly = QHBoxLayout(self.busy_wrap)
        busy_ly.setContentsMargins(10, 0, 0, 0)
        busy_ly.setSpacing(8)
        self.busy_bar = QProgressBar()
        self.busy_bar.setRange(0, 100)
        self.busy_bar.setValue(0)
        self.busy_bar.setFixedWidth(80)
        self.busy_bar.setTextVisible(False)
        busy_ly.addWidget(self.busy_bar)
        self.busy_label = QLabel("")
        self.busy_label.setObjectName("BusyLabel")
        busy_ly.addWidget(self.busy_label)
        self.busy_wrap.setVisible(False)
        ly.addWidget(self.busy_wrap)
        ly.addStretch()

        self.legacy_btn = QPushButton(_t("btn_legacy"))
        self.legacy_btn.clicked.connect(self._on_legacy)
        self.preview_btn = QPushButton(_t("btn_preview"))
        self.preview_btn.clicked.connect(self._on_preview)
        self.export_btn = QPushButton(_t("btn_export"))
        self.export_btn.setObjectName("Primary")
        self.export_btn.clicked.connect(self._on_export)
        for btn in (self.legacy_btn, self.preview_btn, self.export_btn):
            btn.setAutoDefault(False)
            btn.setMinimumWidth(96)
            ly.addWidget(btn)
        return bar

    def _install_shortcuts(self):
        """Mac conventions: ⌘1–5 tabs, ⌘F filter, ⌘P preview, ⌘↩ export, ⌘W close."""
        def bind(seq, slot):
            sc = QShortcut(QKeySequence(seq), self)
            sc.setContext(Qt.ShortcutContext.WindowShortcut)
            sc.activated.connect(slot)
            return sc

        for i in range(self.stack.count()):
            bind("Ctrl+{}".format(i + 1), lambda i=i: self._go_to_tab(i))
        bind(QKeySequence.StandardKey.Find, lambda: (self.filter_edit.setFocus(), self.filter_edit.selectAll()))
        bind(QKeySequence.StandardKey.Close, self.close)
        bind("Ctrl+P", lambda: self.preview_btn.isEnabled() and self.preview_btn.click())
        for seq in ("Ctrl+Return", "Ctrl+Enter"):
            bind(seq, lambda: self.export_btn.isEnabled() and self.export_btn.click())
        native = QKeySequence.SequenceFormat.NativeText
        for btn, seq in ((self.preview_btn, "Ctrl+P"), (self.export_btn, "Ctrl+Return")):
            btn.setToolTip("{}  {}".format(btn.text(), QKeySequence(seq).toString(native)))
        self.filter_edit.returnPressed.connect(self._refresh_count_now)

    def _go_to_tab(self, idx):
        if self.tabs.buttons[idx].isVisibleTo(self.tabs):
            self.tabs.setCurrentIndex(idx)

    def _refresh_count_now(self):
        self._count_timer.stop()
        self._update_count()

    # -------------------------------------------------------- PDF engine
    def _engine_probe(self):
        """Blocking (run in a thread): the parts WeasyPrint needs and whether it actually loads."""
        def first(*paths):
            return next((p for p in paths if p and os.path.exists(p)), None)

        report = {
            "macos": sys.platform == "darwin",
            "brew": first(shutil.which("brew"), "/opt/homebrew/bin/brew", "/usr/local/bin/brew"),
            "python": first("/opt/homebrew/opt/python@3.14/bin/python3.14",
                            "/usr/local/opt/python@3.14/bin/python3.14", shutil.which("python3.14")),
            "pango": bool(first("/opt/homebrew/lib/libpango-1.0.0.dylib",
                                "/usr/local/lib/libpango-1.0.0.dylib")),
        }
        self._weasy_python_cache = None
        logs = []
        try:
            report["engine"] = self._find_weasy_python(logs)
        except Exception as e:
            logs.append(str(e))
            report["engine"] = None
        report["logs"] = logs
        return report

    def _check_engine(self, force=False, then=None):
        """Refresh the engine status without blocking the window (the probe imports WeasyPrint)."""
        callbacks = self.__dict__.setdefault("_engine_callbacks", [])
        if then:
            callbacks.append(then)
        if getattr(self, "_engine_thread", None) is not None:
            return  # a check is already running; its result goes to every waiting caller
        self.engine_status.setText(_t("engine_checking"))
        self.engine_check_btn.setEnabled(False)
        box = {}

        def work():
            box["report"] = self._engine_probe()

        self._engine_thread = threading.Thread(target=work, daemon=True)
        self._engine_thread.start()

        def poll():
            if "report" not in box:
                QTimer.singleShot(150, poll)
                return
            self._engine_thread = None
            self._engine_report = box["report"]
            self.engine_check_btn.setEnabled(True)
            self._show_engine_status()
            waiting, self._engine_callbacks = self._engine_callbacks, []
            for callback in waiting:
                callback(self._engine_report)

        QTimer.singleShot(150, poll)

    def _show_engine_status(self):
        r = self._engine_report or {}
        if r.get("engine"):
            self.engine_status.setText("\u25cf  " + _t("engine_ok"))
            self.engine_status.setStyleSheet("color: #28a745;")
        else:
            self.engine_status.setText("\u25cb  " + _t(
                "engine_missing" if r.get("macos", True) else "eng_unsupported"))
            self.engine_status.setStyleSheet("")
        self.engine_setup_btn.setEnabled(bool(r.get("macos", True)))

    def _open_engine_setup(self):
        dlg = EngineSetupDialog(self)
        dlg.exec()
        self._check_engine(force=True)

    def _create_busy_overlay(self):
        """HUD-style progress panel shown over the window while exporting."""
        self.busy_overlay = QFrame(self)
        self.busy_overlay.setObjectName("BusyOverlay")
        self.busy_overlay.setCursor(Qt.CursorShape.WaitCursor)
        overlay_ly = QVBoxLayout(self.busy_overlay)
        overlay_ly.setContentsMargins(0, 0, 0, 0)
        overlay_ly.addStretch()

        # The progress panel is its own small floating window: it stays in front of the export
        # window (and of Anki) for the whole job, even if the user clicks elsewhere meanwhile.
        self.busy_hud = QWidget(self, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
                                | Qt.WindowType.WindowStaysOnTopHint)
        self.busy_hud.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.busy_hud.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.busy_hud.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)
        hud_ly = QVBoxLayout(self.busy_hud)
        hud_ly.setContentsMargins(0, 0, 0, 0)
        self.busy_panel = macui.RoundedFrame("hud", None, 14, self.busy_hud)
        self.busy_panel.setObjectName("BusyPanel")
        self.busy_panel.setMinimumWidth(280)
        panel_ly = QVBoxLayout(self.busy_panel)
        panel_ly.setContentsMargins(26, 22, 26, 20)
        panel_ly.setSpacing(12)

        self.busy_overlay_label = QLabel("")
        self.busy_overlay_label.setObjectName("BusyOverlayLabel")
        self.busy_overlay_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_ly.addWidget(self.busy_overlay_label)

        self.busy_overlay_bar = QProgressBar()
        self.busy_overlay_bar.setRange(0, 100)
        self.busy_overlay_bar.setValue(0)
        self.busy_overlay_bar.setFixedWidth(220)
        self.busy_overlay_bar.setTextVisible(False)
        panel_ly.addWidget(self.busy_overlay_bar, 0, Qt.AlignmentFlag.AlignCenter)

        hint = QLabel(_t("busy_hint"))
        hint.setObjectName("BusyOverlayHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_ly.addWidget(hint)

        hud_ly.addWidget(self.busy_panel)
        overlay_ly.addStretch()
        self.busy_overlay.setVisible(False)
        self.busy_hud.setVisible(False)
        self._position_busy_overlay()

    def _position_busy_overlay(self):
        if hasattr(self, "busy_overlay"):
            self.busy_overlay.setGeometry(self.rect())
        if hasattr(self, "busy_hud") and self.busy_hud.isVisible():
            self.busy_hud.adjustSize()
            centre = self.frameGeometry().center()
            self.busy_hud.move(centre.x() - self.busy_hud.width() // 2,
                               centre.y() - self.busy_hud.height() // 2)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_busy_overlay()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._position_busy_overlay()

    # ------------------------------------------------------------------ slots
    def _on_width_radio_changed(self, idx, checked):
        if checked:
            self.width_spin.setVisible(idx == 4)

    def _get_card_max_width(self):
        idx = self.width_radio.currentIndex()
        widths = [520, 680, 860, 0, -1]
        val = widths[idx]
        if val == -1:
            return self.width_spin.value()
        return val

    def _on_render_radio_changed(self, idx, checked):
        if not checked or not hasattr(self, "tab_box"):
            return
        tab_idx = self.stack.indexOf(self.fields_tab)
        self.tab_box.setSegmentVisible(tab_idx, idx == 0)
        if idx != 0 and self.stack.currentIndex() == tab_idx:
            self.tabs.setCurrentIndex(0)

    # ------------------------------------------------------------------ decks
    def select_deck(self, name):
        """Reload the deck list and select `name` (a full deck path)."""
        was_loading = self._loading
        self._loading = True
        try:
            self._populate_decks(preferred=name)
        finally:
            self._loading = was_loading

    def refresh_collection(self):
        """Re-read the deck list when the window is shown again; keeps the selection and
        re-detects the note type of the card being studied."""
        self._detect_pending = True
        self.select_deck(self._sel())

    def _populate_decks(self, preferred=None):
        try:
            self._all_decks = sorted(mw.col.decks.all_names_and_ids(), key=lambda d: d.name)
        except Exception as e:
            logger.error("Deck list load failed", e)
            self._all_decks = []
        top = {}
        for d in self._all_decks:
            rn = d.name.split("::")[0]
            if rn not in top:
                top[rn] = d.id
        self.deck_combo.blockSignals(True)
        self.deck_combo.clear()
        for n in sorted(top.keys()):
            self.deck_combo.addItem(n, top[n])
        self.deck_combo.blockSignals(False)
        target = preferred
        if not target:
            try:
                cur = mw.col.decks.current()
                target = cur["name"] if cur else None
            except Exception:
                target = None
        if target:
            i = self.deck_combo.findText(target.split("::")[0])
            if i >= 0:
                self.deck_combo.setCurrentIndex(i)
        self._want_sub = target
        self._on_deck_changed()

    def _on_deck_changed(self, *_):
        rn = self.deck_combo.currentText()
        if not rn:
            self.subdeck_combo.clear()
            self._load_fields()
            self._update_count()
            return
        self.subdeck_combo.blockSignals(True)
        self.subdeck_combo.clear()
        self.subdeck_combo.addItem(_t("entire_deck"), rn)
        pfx = rn + "::"
        for d in self._all_decks:
            if d.name.startswith(pfx):
                sub_name = d.name[len(pfx):]
                parts = sub_name.split("::")
                if len(parts) > 1:
                    display = "    " * (len(parts) - 1) + "↳ " + parts[-1]
                else:
                    display = parts[0]
                self.subdeck_combo.addItem(display, d.name)
        self.subdeck_combo.blockSignals(False)
        for combo in (self.deck_combo, self.subdeck_combo):
            self._fit_popup_width(combo)
        want = getattr(self, "_want_sub", None)
        self._want_sub = None
        if want is None:
            try:
                cur = mw.col.decks.current()
                want = cur["name"] if cur else None
            except Exception:
                want = None
        if want and want.startswith(pfx):
            i = self.subdeck_combo.findData(want)
            if i >= 0:
                self.subdeck_combo.setCurrentIndex(i)
        self._on_subdeck_changed()

    @staticmethod
    def _fit_popup_width(combo):
        """Let the drop-down list be wider than the button so long deck names are readable."""
        view = combo.view()
        widest = max((view.sizeHintForColumn(0) if combo.count() else 0), combo.width())
        view.setMinimumWidth(min(560, widest + 36))

    def _sel(self):
        d = self.subdeck_combo.currentData()
        return d if d else self.deck_combo.currentText()

    def _on_subdeck_changed(self, *_):
        self._load_fields()
        self._update_count()

    # -------------------------------------------------------------- searching
    def _search_query(self, dn=None):
        query = _deck_query(dn or self._sel())
        extra = self.filter_edit.text().strip()
        return "{} ({})".format(query, extra) if extra else query

    def _find_card_ids(self, dn=None):
        ids = list(mw.col.find_cards(self._search_query(dn)))
        order = self.order_combo.currentIndex()
        if order == 1:
            ids.sort()  # card ids are creation timestamps
        elif order == 2:
            random.shuffle(ids)
        return ids

    def _update_count(self):
        dn = self._sel()
        if not dn:
            self._set_count("", False)
            return
        try:
            query = self._search_query(dn)
            cards = len(mw.col.find_cards(query))
            notes = len(mw.col.find_notes(query))
        except Exception as e:
            self.count_label.setToolTip(str(e))
            self._set_count(_t("deck_count_err"), True)
            return
        self.count_label.setToolTip("")
        self._set_count(
            _t("deck_count").format(cards=cards, notes=notes) if cards else _t("deck_count_none"),
            False)

    def _set_count(self, text, error):
        self.count_label.setText(text)
        self.count_label.setProperty("error", bool(error))
        self.count_label.style().unpolish(self.count_label)
        self.count_label.style().polish(self.count_label)

    def _precheck(self):
        """Validate the selection before an export; shows a warning and returns False on problems."""
        dn = self._sel()
        if not dn:
            showWarning(_t("msg_no_cards"))
            return False
        try:
            found = mw.col.find_cards(self._search_query(dn))
        except Exception as e:
            showWarning(_t("msg_bad_search").format(e))
            return False
        if not found:
            showWarning(_t("msg_no_cards"))
            return False
        return True

    # ----------------------------------------------------------------- fields
    def _clear_field_widgets(self):
        for w in self.field_widgets + self._nt_headers:
            w.setParent(None)
            w.deleteLater()
        self.field_widgets.clear()
        self._nt_headers.clear()
        self._fields_compact = None

    def _load_fields(self):
        """Refresh the note-type list for the selected deck and show the chosen type's fields.

        Field settings are remembered per note type, so switching decks (or reopening the
        window) never loses them. Every note type of the collection can be edited; the deck's
        own types are listed first.
        """
        counts = {}
        dn = self._sel()
        if dn:
            try:
                nids = mw.col.find_notes(_deck_query(dn))
                chunk = 500
                for i in range(0, len(nids), chunk):
                    ids = ",".join(str(n) for n in nids[i:i + chunk])
                    for mid, cnt in mw.col.db.all(
                            "SELECT mid, count() FROM notes WHERE id IN ({}) GROUP BY mid".format(ids)):
                        counts[mid] = counts.get(mid, 0) + cnt
            except Exception as e:
                logger.error("Field scan failed for deck {}".format(dn), e)
        self._deck_nt_counts = counts
        deck_ids = [mid for mid, _ in sorted(counts.items(), key=lambda kv: -kv[1])]
        try:
            others = sorted((x for x in mw.col.models.all_names_and_ids() if x.id not in counts),
                            key=lambda x: x.name.lower())
        except Exception:
            others = []

        self.nt_combo.blockSignals(True)
        self.nt_combo.clear()
        for mid in deck_ids:
            nt = mw.col.models.get(mid)
            if nt:
                self.nt_combo.addItem(_t("nt_header").format(name=nt["name"], n=counts[mid]), mid)
        if self.nt_combo.count() and others:
            self.nt_combo.insertSeparator(self.nt_combo.count())
        for x in others:
            self.nt_combo.addItem(x.name, x.id)
        target, source = self._choose_notetype(deck_ids, [x.id for x in others])
        idx = self.nt_combo.findData(target) if target is not None else -1
        self.nt_combo.setCurrentIndex(idx)
        self.nt_combo.blockSignals(False)
        self._show_notetype(target, source)

    @staticmethod
    def _current_card_notetype_id():
        """Note type of the card being reviewed right now, if any."""
        try:
            if getattr(mw, "state", None) != "review":
                return None
            card = getattr(mw.reviewer, "card", None)
            if card is None:
                return None
            nt = card.note_type() if hasattr(card, "note_type") else card.model()
            return nt["id"]
        except Exception:
            return None

    def _choose_notetype(self, deck_ids, other_ids):
        if self._detect_pending:
            self._detect_pending = False
            card_nt = self._current_card_notetype_id()
            if card_nt is not None and (card_nt in deck_ids or card_nt in other_ids):
                self._nt_pinned = "card"
                return card_nt, "card"
        if self._nt_pinned and self._nt_selected in deck_ids:
            return self._nt_selected, ("card" if self._nt_pinned == "card" else None)
        self._nt_pinned = None
        if deck_ids:
            return deck_ids[0], "deck"
        if other_ids:
            return other_ids[0], None
        return None, None

    def _on_notetype_picked(self, idx):
        mid = self.nt_combo.itemData(idx)
        if mid is not None:
            self._nt_pinned = "user"
            self._show_notetype(mid, None)

    def _show_notetype(self, mid, source):
        """Build the field table for one note type."""
        self._clear_field_widgets()
        self._nt_selected = mid
        nt = mw.col.models.get(mid) if mid is not None else None
        self._nt_shown = nt
        if source == "card":
            hint = _t("nt_detect_card")
        elif source == "deck":
            hint = _t("nt_detect_deck")
        elif nt is not None and mid not in self._deck_nt_counts:
            hint = _t("nt_not_in_deck")
        else:
            hint = ""
        self.nt_source.setText(hint)
        self.nt_source.setToolTip(hint)
        is_io = bool(nt) and _notetype_is_io(nt)
        self.nt_reset_btn.setEnabled(bool(nt) and not is_io)
        self.field_preset_btn.setEnabled(bool(nt) and not is_io)
        self.fields_empty.setVisible(nt is None)
        if nt is not None:
            self._add_note_type_group(nt)
            self._reflow_fields(force=True)

    def _add_note_type_group(self, nt):
        table = macui.RoundedFrame("table", "box_border", 8)
        table.setObjectName("Table")
        tl = QVBoxLayout(table)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(0)
        self.fields_layout.insertWidget(self.fields_layout.count() - 1, table)
        self._nt_headers.append(table)
        if _notetype_is_io(nt):
            note = QLabel(_t("nt_io_auto"))
            note.setObjectName("HintLabel")
            note.setWordWrap(True)
            note.setContentsMargins(12, 10, 12, 10)
            tl.addWidget(note)
            return
        saved = _store.get_fields(nt["name"])
        columns = None
        rows = []
        for fld in sorted(nt["flds"], key=lambda f: f["ord"]):
            w = FieldConfigWidget(
                fld["name"], is_front=_is_front_field(fld["name"]),
                nt_id=nt["id"], nt_name=nt["name"], config=saved.get(fld["name"]))
            w.changed.connect(lambda w=w: self._on_field_changed(w))
            tl.addWidget(w)
            w.finalize_columns()
            if columns is None:
                columns = FieldTableHeader(w)
                tl.insertWidget(0, columns)
                self._nt_headers.append(columns)
            rows.append(w)
            self.field_widgets.append(w)
        if rows:
            rows[-1].setProperty("last", True)
            rows[-1].style().unpolish(rows[-1])
            rows[-1].style().polish(rows[-1])

    # ------------------------------------------------------- field presets
    def _field_info(self, text):
        self.fields_info.setText(text)
        self.fields_info.setVisible(True)
        self._fields_info_timer.start(4000)

    def _fill_field_preset_menu(self):
        menu = self.field_preset_menu
        menu.clear()
        names = _store.field_preset_names()
        if names:
            for name in names:
                act = menu.addAction(name)
                act.triggered.connect(lambda _=False, n=name: self._apply_field_preset(n))
        else:
            act = menu.addAction(_t("preset_none"))
            act.setEnabled(False)
        menu.addSeparator()
        save = menu.addAction(_t("btn_preset_save"))
        save.triggered.connect(self._save_field_preset)
        save.setEnabled(bool(self.field_widgets))
        if names:
            delete = menu.addMenu(_t("btn_preset_delete"))
            for name in names:
                act = delete.addAction(name)
                act.triggered.connect(lambda _=False, n=name: self._delete_field_preset(n))

    def _save_field_preset(self, name=None):
        if not self.field_widgets:
            return False
        if name is None:
            name, ok = QInputDialog.getText(self, _t("grp_presets"), _t("preset_prompt"),
                                            text=self._nt_shown["name"] if self._nt_shown else "")
            name = (name or "").strip()
            if not ok or not name:
                return False
            if name in _store.field_presets and not askUser(
                    _t("msg_preset_overwrite").format(name), parent=self):
                return False
        _store.save_field_preset(name, [(w.field_name, w.get_config()) for w in self.field_widgets])
        _store.save()
        self._field_info(_t("msg_preset_saved").format(name))
        return True

    def _apply_field_preset(self, name):
        nt = self._nt_shown
        if not nt or _notetype_is_io(nt):
            return 0
        names = [f["name"] for f in sorted(nt["flds"], key=lambda f: f["ord"])]
        applied = _store.apply_field_preset(name, nt["name"], names)
        if applied:
            _store.save()
            self._show_notetype(nt["id"], None)
            self._field_info(_t("msg_preset_applied").format(name))
        return applied

    def _delete_field_preset(self, name, confirm=True):
        if confirm and not askUser(_t("msg_preset_delete").format(name), parent=self):
            return False
        _store.delete_field_preset(name)
        _store.save()
        self._field_info(_t("msg_preset_deleted").format(name))
        return True

    def _on_field_changed(self, w):
        if self._loading:
            return
        _store.set_field(w.nt_name, w.field_name, w.get_config())
        self._schedule_save()

    def _reset_note_type(self, nt_name):
        _store.reset_fields(nt_name)
        self._schedule_save()
        if self._nt_shown is not None:
            self._show_notetype(self._nt_shown["id"], None)

    # ------------------------------------------------------------------ logs
    def _show_logs(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(_t("logs_title"))
        dlg.resize(700, 500)
        ly = QVBoxLayout(dlg)
        te = QPlainTextEdit()
        te.setReadOnly(True)
        te.setPlainText(logger.text() if logger.entries else _t("no_logs"))
        te.setStyleSheet("font-family:monospace;font-size:12px")
        ly.addWidget(te)
        bb = QHBoxLayout()
        cb = QPushButton(_t("btn_copy"))
        cb.clicked.connect(lambda: QApplication.clipboard().setText(te.toPlainText()))
        bb.addWidget(cb)
        sb = QPushButton(_t("btn_save"))

        def _s():
            p = os.path.join(os.path.expanduser("~/Desktop"), "anki_pdf_log.txt")
            logger.save(p)
            showInfo(_t("msg_log_saved").format(p))

        sb.clicked.connect(_s)
        bb.addWidget(sb)
        bb.addStretch()
        xb = QPushButton(_t("btn_close"))
        xb.clicked.connect(dlg.close)
        bb.addWidget(xb)
        ly.addLayout(bb)
        dlg.exec()

    # ------------------------------------------------------------------ helpers
    def _get_page_dims(self):
        return PAGE_SIZES.get(self.page_combo.currentText(), (210, 297))

    @staticmethod
    def _vendor_dir():
        return os.path.join(os.path.dirname(__file__), ".vendor")

    @staticmethod
    def _isolated_python_env():
        env = os.environ.copy()
        for key in ("PYTHONHOME", "PYTHONPATH"):
            env.pop(key, None)
        env["PYTHONNOUSERSITE"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        path = env.get("PATH", "")
        parts = [p for p in path.split(os.pathsep) if p]
        for extra in (
            "/opt/homebrew/bin", "/opt/homebrew/sbin",
            "/usr/local/bin", "/usr/local/sbin",
            "/usr/bin", "/bin", "/usr/sbin", "/sbin",
        ):
            if extra not in parts:
                parts.append(extra)
        env["PATH"] = os.pathsep.join(parts)
        return env

    @staticmethod
    def _python_command(candidate):
        if not candidate:
            return None
        try:
            parts = shlex.split(candidate)
        except ValueError:
            parts = [candidate]
        if not parts:
            return None
        if os.path.basename(parts[0]) == "env" and len(parts) > 1:
            resolved = shutil.which(parts[1])
            if not resolved:
                return None
            return [resolved] + parts[2:]
        if not os.path.exists(parts[0]):
            resolved = shutil.which(parts[0])
            if not resolved:
                return None
            parts[0] = resolved
        return parts

    def _find_weasy_python(self, logs):
        cached = getattr(self, "_weasy_python_cache", None)
        if cached and os.path.exists(cached):
            return cached

        vendor_dir = self._vendor_dir()
        candidates = []
        launcher_path = os.path.join(vendor_dir, "bin", "weasyprint")
        try:
            with open(launcher_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
            if first_line.startswith("#!"):
                candidates.append(first_line[2:].strip())
        except OSError:
            pass

        for candidate in [
            os.environ.get("ANKI_PDFFER_PYTHON"),
            "/opt/homebrew/opt/python@3.14/bin/python3.14",
            shutil.which("python3.14"),
            "/opt/homebrew/bin/python3",
            "/usr/local/bin/python3",
            shutil.which("python3"),
            "/usr/bin/python3",
        ]:
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        probe = (
            "import os, sys\n"
            "vendor_dir = sys.argv[1]\n"
            "sys.path.insert(0, vendor_dir)\n"
            "from weasyprint import HTML\n"
            "print(sys.executable)\n"
        )
        for candidate in candidates:
            if not candidate:
                continue
            command = self._python_command(candidate)
            if not command:
                continue
            try:
                result = subprocess.run(
                    command + ["-I", "-B", "-c", probe, vendor_dir],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=self._isolated_python_env(),
                )
            except Exception as e:
                logs.append("Weasy probe error [{}]: {}".format(candidate, e))
                continue

            if result.returncode == 0:
                resolved = command[0]
                if result.stdout.strip():
                    resolved = result.stdout.strip().splitlines()[-1].strip() or candidate
                self._weasy_python_cache = resolved if os.path.exists(resolved) else candidate
                logs.append("WeasyPrint python: {}".format(self._weasy_python_cache))
                return self._weasy_python_cache

            detail = (result.stderr or result.stdout or "").strip().splitlines()
            if detail:
                logs.append("Weasy probe reject [{}]: {}".format(candidate, detail[-1][:300]))

        logs.append("WeasyPrint unavailable (no compatible python3)")
        return None

    @staticmethod
    def _safe_filename(name):
        safe = re.sub(r'[\\/:*?"<>|\r\n\t]+', " ", name or "")
        safe = re.sub(r"\s+", " ", safe).strip().strip(".")
        return safe or "export"

    def _theme_index(self):
        idx = self._active_export_theme_index
        if idx is None:
            idx = self.theme_radio.currentIndex()
        return idx if 0 <= idx < len(THEME_PRESETS) else 0

    def _theme_name(self, idx=None):
        idx = self._theme_index() if idx is None else idx
        return THEME_DISPLAY_NAMES[idx] if 0 <= idx < len(THEME_DISPLAY_NAMES) else THEME_DISPLAY_NAMES[0]

    def _font_debug_snapshot(self):
        idx = self.font_combo.currentIndex()
        if not 0 <= idx < len(FONT_OPTIONS):
            idx = 0
        label, stack = FONT_OPTIONS[idx]
        return {
            "index": idx,
            "label": label,
            "stack": stack,
            "size": self.fontsize_spin.value(),
            "families": _real_font_candidates(stack),
            "raw_families": _split_font_stack(stack),
            "debug": self.debug_cb.isChecked(),
        }

    def _qt_font_debug_matches(self, families):
        try:
            try:
                installed = QFontDatabase.families()
            except TypeError:
                installed = QFontDatabase().families()
            installed_by_lower = {name.lower(): name for name in installed}
        except Exception as e:
            return ["Qt font database unavailable: {}".format(e)]

        if not families:
            return ["no concrete font families in CSS stack"]

        matches = []
        for family in families[:8]:
            actual = ""
            try:
                actual = QFontInfo(QFont(family)).family()
            except Exception:
                pass
            installed_name = installed_by_lower.get(family.lower())
            status = "installed" if installed_name else "fallback"
            if actual and actual.lower() == family.lower():
                status = "installed"
            target = actual or installed_name or "n/a"
            matches.append("{} -> {} ({})".format(family, target, status))
        return matches

    def _log_font_debug(self, mode, info):
        key = "{}:{}:{}:{}".format(mode, info["index"], info["size"], info["stack"])
        if key in self._font_debug_logged_modes:
            return
        self._font_debug_logged_modes.add(key)

        logger.log(
            "Font [{}]: {} (index {}, {} px)".format(
                mode, info["label"], info["index"], info["size"]
            )
        )
        logger.log("Font stack [{}]: {}".format(mode, info["stack"]))
        if not self.debug_cb.isChecked():
            return

        candidates = ", ".join(info["families"]) if info["families"] else "(none)"
        logger.log("Font candidates [{}]: {}".format(mode, candidates))
        logger.log("Font import [{}]: Google Inter CSS {}".format(
            mode, "included" if info.get("label") == "Inter" else "skipped"))
        for match in self._qt_font_debug_matches(info["families"]):
            logger.log("Qt font [{}]: {}".format(mode, match))

    def _build_pdf_pagination_script(self):
        pw_mm, ph_mm = self._get_page_dims()
        ppm = 3.7795275591
        page_h_px = ph_mm * ppm
        top_mg_px = self.top_margin_spin.value() * ppm
        content_h_px = page_h_px - (top_mg_px * 2)
        return r"""
(function() {
    var firstPage = document.querySelector('.pdf-page');
    if (!firstPage) {
        return {ok: false, reason: 'missing-page'};
    }

    var pages = Array.from(document.querySelectorAll('.pdf-page'));
    var cards = Array.from(document.querySelectorAll('.card'));
    if (!cards.length) {
        return {ok: true, pages: pages.length, cards: 0, breaks: 0};
    }

    var firstContent = firstPage.querySelector('.page-content');
    var pageContentHeight = %.2f;
    if (!firstContent) {
        return {ok: false, reason: 'missing-content'};
    }
    cards.forEach(function(card) {
        if (card.parentNode) {
            card.parentNode.removeChild(card);
        }
    });

    for (var i = 1; i < pages.length; i += 1) {
        pages[i].remove();
    }

    var currentContent = firstContent;
    var cardsOnPage = 0;
    var breaks = 0;

    function num(v) {
        v = parseFloat(v || '0');
        return isNaN(v) ? 0 : v;
    }

    function usedHeight(content, card) {
        var contentRect = content.getBoundingClientRect();
        var cardRect = card.getBoundingClientRect();
        var cardStyle = window.getComputedStyle(card);
        return Math.ceil(cardRect.bottom - contentRect.top + num(cardStyle.marginBottom));
    }

    function createPage() {
        var page = document.createElement('div');
        page.className = 'pdf-page';
        var content = document.createElement('div');
        content.className = 'page-content';
        page.appendChild(content);
        firstPage.parentNode.appendChild(page);
        return {page: page, content: content};
    }

    cards.forEach(function(card) {
        currentContent.appendChild(card);
        var used = usedHeight(currentContent, card);
        if (cardsOnPage > 0 && used > pageContentHeight + 1) {
            currentContent.removeChild(card);
            var next = createPage();
            currentContent = next.content;
            currentContent.appendChild(card);
            cardsOnPage = 1;
            breaks += 1;
        } else {
            cardsOnPage += 1;
        }
    });

    return {
        ok: true,
        pages: document.querySelectorAll('.pdf-page').length,
        cards: cards.length,
        breaks: breaks,
        pageHeight: %.2f,
        contentHeight: pageContentHeight,
        topMargin: %.2f,
        firstPageHeight: Math.ceil(firstContent.getBoundingClientRect().height || 0)
    };
})();
""" % (content_h_px, page_h_px, top_mg_px)

    def _build_pdf_ready_script(self):
        return r"""
(function() {
    var images = Array.from(document.images || []);
    var pendingImages = images.filter(function(img) {
        return !img.complete;
    }).length;
    var fontsLoaded = true;
    var fontFaces = [];
    if (document.fonts && document.fonts.status) {
        fontsLoaded = document.fonts.status === 'loaded';
        if (document.fonts.forEach) {
            document.fonts.forEach(function(face) {
                fontFaces.push({
                    family: face.family,
                    status: face.status,
                    weight: face.weight,
                    style: face.style
                });
            });
        }
    }
    return {
        ready: fontsLoaded && pendingImages === 0,
        fontsLoaded: fontsLoaded,
        pendingImages: pendingImages,
        imageCount: images.length,
        fontFaces: fontFaces.slice(0, 12)
    };
})();
"""

    def _set_btns(self, on):
        self.legacy_btn.setEnabled(on)
        self.preview_btn.setEnabled(on)
        self.export_btn.setEnabled(on)
        self.grid_cb.setEnabled(on)

    def _animate_busy(self):
        self._busy_val = min(95.0, self._busy_val + (95.0 - self._busy_val) * 0.025)
        if hasattr(self, "busy_overlay_bar"):
            self.busy_overlay_bar.setValue(int(self._busy_val))
        if hasattr(self, "busy_bar"):
            self.busy_bar.setValue(int(self._busy_val))
        if hasattr(self, "busy_hud") and self._busy_depth and self.isVisible() \
                and not self.busy_hud.isVisible():
            self.busy_hud.show()
            self._position_busy_overlay()
        if hasattr(self, "busy_hud") and self._busy_depth:
            self.busy_hud.raise_()
        if hasattr(self, "busy_overlay_label"):
            self.busy_overlay_label.setText(self._base_busy_message or "")

    def _set_busy_message(self, message):
        self._base_busy_message = message
        self.busy_label.setText(message)
        self.busy_wrap.setVisible(True)
        if hasattr(self, "busy_overlay"):
            self.busy_overlay_label.setText(message)
            self.busy_overlay.setVisible(True)
            self.busy_overlay.raise_()
            self.busy_hud.show()
            self.busy_hud.raise_()
            self._position_busy_overlay()
        QApplication.processEvents()

    def _begin_busy(self, message):
        if self._busy_depth == 0:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self._busy_val = 3.0
            if self.isVisible():
                self.raise_()
            if hasattr(self, "_busy_timer"):
                self._busy_timer.start(80)
        self._busy_depth += 1
        self._set_btns(False)
        self._set_busy_message(message)

    def _end_busy(self, force=False):
        if force:
            self._busy_depth = 0
        elif self._busy_depth > 0:
            self._busy_depth -= 1
        if self._busy_depth > 0:
            return
        if hasattr(self, "_busy_timer"):
            self._busy_timer.stop()
        self.busy_wrap.setVisible(False)
        if hasattr(self, "busy_overlay"):
            self.busy_overlay.setVisible(False)
            self.busy_hud.setVisible(False)
            self.busy_overlay_bar.setValue(0)
        self.busy_label.setText("")
        self._set_btns(True)
        try:
            QApplication.restoreOverrideCursor()
        except Exception:
            pass
        QApplication.processEvents()

    def _bring_to_front(self):
        QTimer.singleShot(300, lambda: (self.raise_(), self.activateWindow()))

    def _save_debug_artifacts(self, mode, card_ids, html_output):
        if not self.debug_cb.isChecked():
            return
        try:
            desktop = os.path.expanduser("~/Desktop")
            short = self._safe_filename(self._sel().split("::")[-1])
            ts = datetime.datetime.now().strftime("%H%M%S")
            html_path = os.path.join(desktop, "anki_debug_{}_{}.html".format(short, ts))
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_output)
            logger.save(os.path.join(desktop, "anki_pdf_log.txt"))
        except Exception as e:
            logger.log("Failed to save debug artifacts: {}".format(e))

    # ------------------------------------------------------------------ actions
    def _on_legacy(self):
        if not self._precheck():
            return
        try:
            self._begin_busy(_t("busy_legacy"))
            logger.start("Legacy")
            self._font_debug_logged_modes = set()
            self._active_export_theme_index = self.theme_radio.currentIndex()
            logger.log("Build: {}".format(EXPORT_BUILD))
            logger.log("Theme: {} ({})".format(self._theme_name(), self._theme_index()))
            html, card_ids = self._build_html(mode="legacy")
            self._set_busy_message(_t("busy_opening"))
            fd, p = tempfile.mkstemp(suffix=".html", text=True)
            os.close(fd)
            with open(p, "w", encoding="utf-8") as f:
                f.write(html)
            logger.finish()
            self._save_debug_artifacts("legacy", card_ids, html)
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))
            self._bring_to_front()
        except Exception as e:
            logger.error("Legacy", e)
            logger.finish()
            showWarning(str(e))
        finally:
            self._end_busy(force=True)

    def _on_preview(self):
        """Preview is the real PDF: same HTML, same engine and layout pass as Export, written to a
        temporary file and opened. (An HTML mock-up paginated by estimates never matched.)"""
        if not self._precheck():
            return
        dn = self._sel()
        short = self._safe_filename(dn.split("::")[-1] if "::" in dn else dn)
        path = os.path.join(tempfile.gettempdir(), "AnkiPdffer-preview-{}.pdf".format(short))
        logger.start("Preview")
        self._font_debug_logged_modes = set()
        self._preview_pending = True
        self._begin_busy(_t("busy_preview"))
        try:
            QApplication.processEvents()
            self._active_export_theme_index = self.theme_radio.currentIndex()
            logger.log("Build: {}".format(EXPORT_BUILD))
            logger.log("Theme: {} ({})".format(self._theme_name(), self._theme_index()))
            html, card_ids = self._build_html(mode="pdf")
            fd, self.temp_html_path = tempfile.mkstemp(suffix=".html", text=True)
            os.close(fd)
            with open(self.temp_html_path, "w", encoding="utf-8") as f:
                f.write(html)
            self._save_debug_artifacts("preview", card_ids, html)
            self._start_external_export(path)
        except Exception as e:
            self._preview_pending = False
            logger.error("Preview", e)
            logger.finish()
            self._save_debug_log()
            showWarning(str(e))
            self._reset()

    @staticmethod
    def _export_dir():
        """Where the save dialog starts: the last export folder, else Desktop (Anki's own working
        directory is the disk root, which a regular user cannot write to)."""
        home = os.path.expanduser("~")
        for folder in (_store.settings.get("export_dir"), os.path.join(home, "Desktop"),
                       os.path.join(home, "Documents"), home):
            if folder and os.path.isdir(folder) and os.access(folder, os.W_OK):
                return folder
        return home

    def _on_export(self):
        if not self._precheck():
            return
        dn = self._sel()
        short = self._safe_filename(dn.split("::")[-1] if "::" in dn else dn)
        uid = str(uuid.uuid4()).split('-')[0][:6]
        sp, _ = QFileDialog.getSaveFileName(
            self, _t("dlg_save_pdf"), os.path.join(self._export_dir(), "{}_{}.pdf".format(short, uid)),
            _t("pdf_filter"))
        if not sp:
            return
        if not sp.lower().endswith(".pdf"):
            sp += ".pdf"
        _store.update_settings({"export_dir": os.path.dirname(sp)})
        _store.save()
        logger.start("Export")
        self._font_debug_logged_modes = set()
        self._preview_pending = False
        self._begin_busy(_t("busy_pdf_html"))
        self.export_btn.setText(_t("generating"))
        try:
            QApplication.processEvents()
            self._active_export_theme_index = self.theme_radio.currentIndex()
            logger.log("Build: {}".format(EXPORT_BUILD))
            logger.log("Theme: {} ({})".format(self._theme_name(), self._theme_index()))
            html, card_ids = self._build_html(mode="pdf")
            fd, self.temp_html_path = tempfile.mkstemp(suffix=".html", text=True)
            os.close(fd)
            with open(self.temp_html_path, "w", encoding="utf-8") as f:
                f.write(html)
            self._save_debug_artifacts("pdf", card_ids, html)
            self._start_external_export(sp)
        except Exception as e:
            logger.error("Export", e)
            logger.finish()
            self._save_debug_log()
            showWarning(str(e))
            self._reset()

    def _start_qt_pdf_export(self, path):
        logger.log("Generating Qt WebEngine fallback layout")
        self._pdf_ready_logged = False
        html, _ = self._build_html(mode="pdf_fallback")
        fd, self.temp_fallback_path = tempfile.mkstemp(suffix=".html", text=True)
        os.close(fd)
        with open(self.temp_fallback_path, "w", encoding="utf-8") as f:
            f.write(html)

        self.page = CustomWebEnginePage()
        try:
            self.page.settings().setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        except AttributeError:
            pass
        _bg = _theme_tokens(self._theme_index())["body"]
        try:
            self.page.setBackgroundColor(QColor(_bg))
        except Exception:
            pass
        self.page.loadFinished.connect(lambda ok: self._loaded(ok, path))
        self.page.load(QUrl.fromLocalFile(self.temp_fallback_path))

    def _loaded(self, ok, path):
        if not ok:
            logger.error("Load fail")
            logger.finish()
            self._save_debug_log()
            showWarning(_t("msg_error"))
            self._reset()
            return
        self._wait_for_pdf_layout(path, 0)

    def _wait_for_pdf_layout(self, path, attempt):
        try:
            self.page.runJavaScript(
                self._build_pdf_ready_script(),
                lambda result, attempt=attempt: self._after_pdf_ready(path, attempt, result),
            )
        except TypeError:
            if attempt < 6:
                QTimer.singleShot(150, lambda: self._wait_for_pdf_layout(path, attempt + 1))
            else:
                QTimer.singleShot(150, lambda: self._do_print(path))

    def _after_pdf_ready(self, path, attempt, result):
        if result and (result.get("ready") or attempt >= 20) and not self._pdf_ready_logged:
            self._pdf_ready_logged = True
            faces = result.get("fontFaces") or []
            face_bits = []
            for face in faces[:6]:
                if isinstance(face, dict):
                    face_bits.append(
                        "{}:{}:{}:{}".format(
                            face.get("family", ""),
                            face.get("status", ""),
                            face.get("weight", ""),
                            face.get("style", ""),
                        )
                    )
            logger.log(
                "Qt PDF ready: fontsLoaded={}, pendingImages={}, imageCount={}, fontFaces={}".format(
                    result.get("fontsLoaded"),
                    result.get("pendingImages"),
                    result.get("imageCount"),
                    "; ".join(face_bits) if face_bits else "(none)",
                )
            )
        if result and result.get("ready"):
            QTimer.singleShot(150, lambda: self._do_print(path))
            return
        if attempt < 20:
            QTimer.singleShot(100, lambda: self._wait_for_pdf_layout(path, attempt + 1))
            return
        if result:
            logger.log("Layout wait timeout: {}".format(result))
        QTimer.singleShot(150, lambda: self._do_print(path))

    def _start_external_export(self, path):
        if not getattr(self, "_preview_pending", False):
            self.export_btn.setText(_t("printing"))
        self._set_busy_message(_t("busy_pdf_render"))
        self._external_export_result = None
        html_path = self.temp_html_path
        font_debug = self._font_debug_snapshot()
        worker = threading.Thread(
            target=self._run_external_export_job,
            args=(html_path, path, font_debug),
            daemon=True,
        )
        self._external_export_thread = worker
        worker.start()
        QTimer.singleShot(100, lambda: self._poll_external_export(path))

    def _poll_external_export(self, path):
        result = getattr(self, "_external_export_result", None)
        if result is None:
            QTimer.singleShot(100, lambda: self._poll_external_export(path))
            return

        self._external_export_result = None
        self._external_export_thread = None
        for entry in result.get("logs", []):
            logger.log(entry)

        if result.get("success") and os.path.exists(path):
            self._printed(path, True)
            return

        self._start_qt_pdf_export(path)

    def _run_external_export_job(self, html_path, path, font_debug):
        logs = []
        try:
            ok = self._export_pdf_via_weasyprint(path, html_path, logs, font_debug)
            if ok:
                self._external_export_result = {"success": True, "logs": logs}
                return
        except Exception as e:
            logs.append("External export exception: {}".format(e))
        self._external_export_result = {"success": False, "logs": logs}

    def _export_pdf_via_weasyprint(self, path, html_path, logs, font_debug):
        vendor_dir = self._vendor_dir()
        if not os.path.isdir(vendor_dir):
            logs.append("PDF engine: WeasyPrint unavailable (.vendor missing)")
            return False

        python_bin = self._find_weasy_python(logs)
        if not python_bin:
            return False

        logs.append("PDF engine: WeasyPrint")
        script = (
            "import json, os, shutil, subprocess, sys, tempfile\n"
            "from xml.sax.saxutils import escape\n"
            "vendor_dir, html_path, pdf_path, font_json, layout_json = sys.argv[1:6]\n"
            "sys.path.insert(0, vendor_dir)\n"
            "try:\n"
            "    font_info = json.loads(font_json)\n"
            "except Exception:\n"
            "    font_info = {}\n"
            "def font_log(message):\n"
            "    print('Font debug: {}'.format(message), flush=True)\n"
            "def fontconfig_override(families):\n"
            "    families = [f for f in families if f]\n"
            "    if not families:\n"
            "        return None\n"
            "    config_candidates = [\n"
            "        os.environ.get('FONTCONFIG_FILE'),\n"
            "        '/opt/homebrew/etc/fonts/fonts.conf',\n"
            "        '/usr/local/etc/fonts/fonts.conf',\n"
            "        '/etc/fonts/fonts.conf',\n"
            "    ]\n"
            "    include_path = next((p for p in config_candidates if p and os.path.exists(p)), None)\n"
            "    fd, config_path = tempfile.mkstemp(prefix='anki-pdffer-fonts-', suffix='.conf')\n"
            "    with os.fdopen(fd, 'w', encoding='utf-8') as config:\n"
            "        config.write('<?xml version=\"1.0\"?>\\n')\n"
            "        config.write('<!DOCTYPE fontconfig SYSTEM \"urn:fontconfig:fonts.dtd\">\\n')\n"
            "        config.write('<fontconfig>\\n')\n"
            "        if include_path:\n"
            "            config.write('  <include>{}</include>\\n'.format(escape(include_path)))\n"
            "        else:\n"
            "            for font_dir in ('/System/Library/Fonts', '/Library/Fonts', os.path.expanduser('~/Library/Fonts')):\n"
            "                if os.path.isdir(font_dir):\n"
            "                    config.write('  <dir>{}</dir>\\n'.format(escape(font_dir)))\n"
            "        seen = set()\n"
            "        for family in families:\n"
            "            family_key = family.lower()\n"
            "            if family_key in seen:\n"
            "                continue\n"
            "            seen.add(family_key)\n"
            "            family_xml = escape(family)\n"
            "            config.write('  <match target=\"pattern\">\\n')\n"
            "            config.write('    <test name=\"family\" compare=\"eq\"><string>{}</string></test>\\n'.format(family_xml))\n"
            "            config.write('    <edit name=\"genericfamily\" mode=\"assign_replace\"><int>0</int></edit>\\n')\n"
            "            config.write('  </match>\\n')\n"
            "        config.write('</fontconfig>\\n')\n"
            "    os.environ['FONTCONFIG_FILE'] = config_path\n"
            "    return config_path\n"
            "font_config_path = fontconfig_override(font_info.get('families') or [])\n"
            "try:\n"
            "    if font_config_path and font_info.get('debug'):\n"
            "        font_log('fontconfig override {}'.format(font_config_path))\n"
            "        font_log('fontconfig exact families {}'.format(', '.join(font_info.get('families') or [])))\n"
            "    if font_info.get('debug'):\n"
            "        font_log('selected {} (index {}, {} px)'.format(\n"
            "            font_info.get('label', '?'), font_info.get('index', '?'), font_info.get('size', '?')))\n"
            "        font_log('CSS stack {}'.format(font_info.get('stack', '')))\n"
            "        families = font_info.get('families') or []\n"
            "        fc_match = shutil.which('fc-match')\n"
            "        if fc_match and families:\n"
            "            for family in families[:8]:\n"
            "                try:\n"
            "                    match = subprocess.run(\n"
            "                        [fc_match, family], capture_output=True, text=True, timeout=5)\n"
            "                    detail = (match.stdout or match.stderr or '').strip().splitlines()\n"
            "                    font_log('fc-match {} -> {}'.format(family, detail[0] if detail else 'no output'))\n"
            "                except Exception as e:\n"
            "                    font_log('fc-match {} error: {}'.format(family, e))\n"
            "        elif not fc_match:\n"
            "            font_log('fc-match unavailable')\n"
            "        else:\n"
            "            font_log('no concrete font families in CSS stack')\n"
            "    from weasyprint import HTML\n"
            + _LAYOUT_PASS_SCRIPT +
            "    write_optimised(HTML, html_path, pdf_path, layout_json)\n"
            "finally:\n"
            "    if font_config_path:\n"
            "        try:\n"
            "            os.remove(font_config_path)\n"
            "        except OSError:\n"
            "            pass\n"
        )
        try:
            if os.path.exists(path):
                os.remove(path)
            command = self._python_command(python_bin)
            if not command:
                logs.append("WeasyPrint export error: invalid python [{}]".format(python_bin))
                return False
            result = subprocess.run(
                command + [
                    "-I", "-B", "-c", script, vendor_dir, html_path, path,
                    json.dumps(font_debug, sort_keys=True),
                    json.dumps(getattr(self, "_last_layout", None) or {}),
                ],
                capture_output=True,
                text=True,
                timeout=120,
                env=self._isolated_python_env(),
            )
            if result.stdout:
                for line in result.stdout.strip().splitlines():
                    logs.append(line[:1000])
            if result.returncode == 0 and result.stderr and font_debug.get("debug"):
                logs.append("WeasyPrint stderr: {}".format(result.stderr.strip()[:2000]))
            if result.returncode != 0:
                logs.append("WeasyPrint exit: {}".format(result.returncode))
                if result.stderr:
                    logs.append("WeasyPrint stderr: {}".format(result.stderr.strip()[:2000]))
                if result.stdout:
                    logs.append("WeasyPrint stdout: {}".format(result.stdout.strip()[:2000]))
                return False
            if os.path.exists(path):
                return True
        except Exception as e:
            logs.append("WeasyPrint export error: {}".format(e))
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
        logs.append("PDF engine: WeasyPrint failed")
        return False

    def _do_print(self, path):
        self.export_btn.setText(_t("printing"))
        self._set_busy_message(_t("busy_pdf_render"))
        try:
            # Try PyQt6 first
            from PyQt6.QtCore import QMarginsF
            from PyQt6.QtGui import QPageLayout, QPageSize

            ps_map = {
                "A4": QPageSize.PageSizeId.A4,
                "Letter": QPageSize.PageSizeId.Letter,
                "A3": QPageSize.PageSizeId.A3,
                "A5": QPageSize.PageSizeId.A5,
            }
            size = QPageSize(ps_map.get(self.page_combo.currentText(), QPageSize.PageSizeId.A4))
            layout = QPageLayout(
                size,
                QPageLayout.Orientation.Portrait,
                QMarginsF(0, 0, 0, 0),
                QPageLayout.Unit.Millimeter,
            )

            try:
                self.page.pdfPrintingFinished.disconnect(self._printed)
            except Exception:
                pass
            self.page.pdfPrintingFinished.connect(self._printed)
            self.page.printToPdf(path, layout)

        except (ImportError, AttributeError):
            try:
                # Fallback to PyQt5
                from PyQt5.QtCore import QMarginsF
                from PyQt5.QtGui import QPageLayout, QPageSize

                ps_map = {
                    "A4": QPageSize.A4,
                    "Letter": QPageSize.Letter,
                    "A3": QPageSize.A3,
                    "A5": QPageSize.A5,
                }
                psid_val = ps_map.get(self.page_combo.currentText(), QPageSize.A4)

                size = QPageSize(psid_val)
                layout = QPageLayout(
                    size,
                    QPageLayout.Orientation.Portrait,
                    QMarginsF(0, 0, 0, 0),
                    QPageLayout.Unit.Millimeter,
                )

                try:
                    self.page.pdfPrintingFinished.disconnect(self._printed)
                except Exception:
                    pass
                self.page.pdfPrintingFinished.connect(self._printed)
                self.page.printToPdf(path, layout)
            except Exception:
                # Minimal fallback - likely to have white margins but better than crash
                try:
                    self.page.pdfPrintingFinished.disconnect(self._printed)
                except Exception:
                    pass
                if hasattr(self.page, 'pdfPrintingFinished'):
                    self.page.pdfPrintingFinished.connect(self._printed)
                self.page.printToPdf(path)
    def _printed(self, path, success):
        if success and os.path.exists(path):
            logger.log("PDF path: {}".format(path))
            logger.log("PDF: {} B".format(os.path.getsize(path)))
        logger.finish()
        self._save_debug_log()
        self._reset()
        for attr in ("temp_html_path", "temp_fallback_path"):
            tmp = getattr(self, attr, None)
            if tmp:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
                setattr(self, attr, None)
        preview = getattr(self, "_preview_pending", False)
        self._preview_pending = False
        if success:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            self._bring_to_front()
            if not preview:
                showInfo(_t("msg_pdf_saved").format(path))

    def _save_debug_log(self):
        try:
            logger.save(os.path.join(os.path.dirname(__file__), "last_export_log.txt"))
        except Exception:
            pass
        try:
            if self.debug_cb.isChecked():
                logger.save(os.path.join(os.path.expanduser("~/Desktop"), "anki_pdf_log.txt"))
        except Exception as e:
            logger.log("Failed to save debug log: {}".format(e))

    def _reset(self):
        self.export_btn.setText(_t("btn_export"))
        self._active_export_theme_index = None
        self._end_busy(force=True)

    def _collect_fc(self):
        """{note type id: {field name: config}}: what is remembered for every note type, with
        the rows on screen taking precedence. Fields never touched fall back to the automatic
        front/back guess at export time."""
        fc = {}
        try:
            for item in mw.col.models.all_names_and_ids():
                saved = _store.get_fields(item.name)
                if saved:
                    fc[item.id] = saved
        except Exception as e:
            logger.error("Note type list failed", e)
        for w in self.field_widgets:
            fc.setdefault(w.nt_id, {})[w.field_name] = w.get_config()
        return fc

    # ------------------------------------------------------------------ settings
    def _get_all_settings(self):
        return {
            "theme": self.theme_radio.currentIndex(),
            "font": self.font_combo.currentIndex(),
            "font_size": self.fontsize_spin.value(),
            "width": self.width_radio.currentIndex(),
            "custom_width": self.width_spin.value(),
            "layout": self.layout_radio.currentIndex(),
            "render": self.render_radio.currentIndex(),
            "show_title": self.show_title_cb.isChecked(),
            "card_numbers": self.card_numbers_cb.isChecked(),
            "zebra": self.zebra_cb.isChecked(),
            "page": self.page_combo.currentIndex(),
            "margins": self.margin_spin.value(),
            "top_margin": self.top_margin_spin.value(),
            "padding": self.padding_spin.value(),
            "min_gap": self.gap_spin.value(),
            "line_height": self.lh_spin.value(),
            "max_img": self.img_h_spin.value(),
            "strip_html": self.strip_html_cb.isChecked(),
            "card_style": self.card_style_combo.currentIndex(),
            "grid": self.grid_cb.isChecked(),
            "language": self.lang_combo.currentData() or "en",
            "debug": self.debug_cb.isChecked(),
            "high_contrast": self.high_contrast_cb.isChecked(),
            "qa_layout": self.qa_combo.currentIndex(),
            "cloze_mode": self.cloze_combo.currentIndex(),
            "io_mode": self.io_combo.currentIndex(),
            "order": self.order_combo.currentIndex(),
            "page_numbers": self.page_numbers_cb.isChecked(),
            "tab": self.tabs.currentIndex(),
        }

    @staticmethod
    def _set_combo(combo, idx):
        if 0 <= idx < combo.count():
            combo.setCurrentIndex(idx)

    def _apply_settings(self, s):
        """Push a settings dict into the widgets (autosave stays off while doing so)."""
        s = coerce_settings(s)
        was_loading = self._loading
        self._loading = True
        try:
            self.theme_radio.setCurrentIndex(s["theme"])
            self._set_combo(self.font_combo, s["font"])
            self.fontsize_spin.setValue(s["font_size"])
            self.width_radio.setCurrentIndex(s["width"])
            self.width_spin.setValue(s["custom_width"])
            self.layout_radio.setCurrentIndex(s["layout"])
            self.render_radio.setCurrentIndex(s["render"])
            self.show_title_cb.setChecked(s["show_title"])
            self.card_numbers_cb.setChecked(s["card_numbers"])
            self.zebra_cb.setChecked(s["zebra"])
            self._set_combo(self.page_combo, s["page"])
            self.margin_spin.setValue(s["margins"])
            self.top_margin_spin.setValue(s["top_margin"])
            self.padding_spin.setValue(s["padding"])
            self.gap_spin.setValue(s["min_gap"])
            self.lh_spin.setValue(s["line_height"])
            self.img_h_spin.setValue(s["max_img"])
            self.strip_html_cb.setChecked(s["strip_html"])
            self._set_combo(self.card_style_combo, s["card_style"])
            self.grid_cb.setChecked(s["grid"])
            self.debug_cb.setChecked(s["debug"])
            self.high_contrast_cb.setChecked(s["high_contrast"])
            self._set_combo(self.qa_combo, s["qa_layout"])
            self._set_combo(self.cloze_combo, s["cloze_mode"])
            self._set_combo(self.io_combo, s["io_mode"])
            self._set_combo(self.order_combo, s["order"])
            self.page_numbers_cb.setChecked(s["page_numbers"])
            if 0 <= s["tab"] < self.stack.count() and self.tabs.buttons[s["tab"]].isVisibleTo(self.tabs):
                self.tabs.setCurrentIndex(s["tab"])
            self.lang_combo.blockSignals(True)
            self._set_combo(self.lang_combo, self.lang_combo.findData(s["language"]))
            self.lang_combo.blockSignals(False)
            self.log_btn.setVisible(self.debug_cb.isChecked())
        finally:
            self._loading = was_loading

    def _connect_autosave(self):
        sched = self._schedule_save
        for rg in (self.theme_radio, self.width_radio, self.layout_radio, self.render_radio, self.tabs):
            rg.group.idToggled.connect(sched)
        for cb in (self.show_title_cb, self.card_numbers_cb, self.zebra_cb, self.high_contrast_cb,
                   self.strip_html_cb, self.grid_cb, self.debug_cb, self.page_numbers_cb):
            cb.toggled.connect(sched)
        for sp in (self.fontsize_spin, self.width_spin, self.margin_spin, self.top_margin_spin,
                   self.padding_spin, self.gap_spin, self.lh_spin, self.img_h_spin):
            sp.valueChanged.connect(sched)
        for combo in (self.font_combo, self.page_combo, self.card_style_combo, self.qa_combo,
                      self.cloze_combo, self.io_combo, self.order_combo):
            combo.currentIndexChanged.connect(sched)
        self.order_combo.currentIndexChanged.connect(lambda *_: None)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)

    def _schedule_save(self, *_):
        if not self._loading:
            self._save_timer.start(400)

    def _flush_save(self):
        """Write the current UI state (options, remembered fields, window size) to disk."""
        self._save_timer.stop()
        if self._loading:
            return
        _store.update_settings(self._get_all_settings())
        try:
            _store.set_geometry(self.saveGeometry())
        except Exception:
            pass
        err = _store.save()
        if err:
            logger.log("Settings save failed: {}".format(err))

    def hideEvent(self, event):
        super().hideEvent(event)
        if hasattr(self, "busy_hud"):
            self.busy_hud.hide()  # a separate window: it does not hide with its owner
        self._flush_save()

    def closeEvent(self, event):
        self._flush_save()
        super().closeEvent(event)

    def _on_language_changed(self, *_):
        if self._loading:
            return
        code = self.lang_combo.currentData() or "en"
        _store.update_settings({"language": code})
        self._flush_save()
        _set_language(code)
        QTimer.singleShot(0, _rebuild_dialog)

    def _info(self, text):
        self.settings_info.setText(text)
        self.settings_info.setVisible(True)

    # ------------------------------------------------------------------ presets
    def _refresh_presets(self, select=None):
        names = _store.preset_names()
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        if names:
            self.preset_combo.addItems(names)
            if select in names:
                self.preset_combo.setCurrentIndex(names.index(select))
        else:
            self.preset_combo.addItem(_t("preset_none"))
        self.preset_combo.blockSignals(False)
        for btn in (self.preset_apply_btn, self.preset_delete_btn):
            btn.setEnabled(bool(names))
        self.preset_combo.setEnabled(bool(names))

    def _selected_preset(self):
        return self.preset_combo.currentText() if _store.presets else None

    def _save_preset(self):
        self._loading = False
        self._flush_save()
        name, ok = QInputDialog.getText(self, _t("grp_presets"), _t("preset_prompt"))
        name = (name or "").strip()
        if not ok or not name:
            return
        if name in _store.presets and not askUser(_t("msg_preset_overwrite").format(name), parent=self):
            return
        _store.save_preset(name)
        _store.save()
        self._refresh_presets(select=name)
        self._info(_t("msg_preset_saved").format(name))

    def _apply_preset(self):
        name = self._selected_preset()
        if not name or not _store.apply_preset(name):
            return
        self._apply_settings(_store.settings)
        self._load_fields()
        self._update_count()
        _store.save()
        self._info(_t("msg_preset_applied").format(name))

    def _delete_preset(self):
        name = self._selected_preset()
        if not name or not askUser(_t("msg_preset_delete").format(name), parent=self):
            return
        _store.delete_preset(name)
        _store.save()
        self._refresh_presets()
        self._info(_t("msg_preset_deleted").format(name))

    def _reset_settings(self):
        if not askUser(_t("msg_reset_confirm"), parent=self):
            return
        _store.reset_settings()
        _store.reset_fields()
        self._apply_settings(_store.settings)
        self._load_fields()
        self._update_count()
        _store.save()
        self._info(_t("msg_settings_reset"))

    # ================================================================== HTML
    def _build_html(self, mode="pdf"):
        deck_name = self._sel()
        media_dir = mw.col.media.dir()
        render_mode = self.render_radio.currentIndex()
        fc = self._collect_fc()
        compact = self.layout_radio.currentIndex() == 1
        theme_idx = self._theme_index()

        font_info = self._font_debug_snapshot()
        font = font_info["stack"]
        bsz = font_info["size"]
        self._log_font_debug(mode, font_info)
        pad = self.padding_spin.value()
        padh = max(4, pad - 4)
        min_gap = self.gap_spin.value()
        css_gap = min_gap
        card_gap = css_gap
        lh = self.lh_spin.value()
        img_h = self.img_h_spin.value()
        ps = self.page_combo.currentText()
        mg = self.margin_spin.value()
        top_mg = self.top_margin_spin.value()
        show_title = self.show_title_cb.isChecked()
        show_nums = self.card_numbers_cb.isChecked()
        zebra = self.zebra_cb.isChecked()
        strip = self.strip_html_cb.isChecked()
        high_contrast = self.high_contrast_cb.isChecked()
        card_max_w = self._get_card_max_width()

        pw_mm, ph_mm = self._get_page_dims()
        ppm = 3.7795275591
        page_w_px = pw_mm * ppm
        page_h_px = ph_mm * ppm
        mg_px = mg * ppm
        top_mg_px = top_mg * ppm
        t = _theme_tokens(theme_idx)
        grid_mode = self.grid_cb.isChecked() if mode == "legacy" else False

        cs = self.card_style_combo.currentIndex()
        card_styles = [
            "border-radius:12px;box-shadow:{};border:1px solid {};".format(t["shadow"], t["brd"]),
            "border-radius:0;border:1px solid {};".format(t["brd"]),
            "border:none;border-bottom:2px solid {};border-radius:0;box-shadow:none;".format(t["accent_brd"]),
            "border-radius:10px;border:2px double {};box-shadow:none;".format(t["accent_brd"]),
            "border:none;border-radius:0;box-shadow:none;",
        ]
        card_extra = card_styles[cs]

        bg_map = ["__auto__", "#ffffff", "#f8f9fa", "#f0f4ff", "#fffde7", "#f0fdf4", "#fff5f5", "#f5f3ff"]
        sz_map = ["0.8em", "1em", "1.15em", "1.4em"]
        cl_map = ["inherit", "#9ca3af", "#ef4444", "#3b82f6", "#22c55e", "#f97316", "#8b5cf6"]
        al_map = ["left", "center", "justify", "right"]

        display_title = deck_name.split("::")[-1] if "::" in deck_name else deck_name
        deck_path = deck_name.replace("::", " > ")
        label_sz = max(8, bsz - 4)
        title_gap = 4

        if card_max_w > 0:
            content_max_w_css = ".page-content{{max-width:{mw}px;margin:0 auto}}".format(mw=card_max_w)
        else:
            content_max_w_css = ""

        font_import = (
            "@import url('https://fonts.googleapis.com/css2?"
            "family=Inter:wght@400;500;600;700;800&display=swap');"
            if font_info.get("label") == "Inter" else ""  # System etc. only *list* Inter
        )
        page_numbers = self.page_numbers_cb.isChecked() and mode == "pdf"
        bottom_mm = max(top_mg, 12) if page_numbers else max(top_mg, 9)
        generator = " \u00b7 ".join([
            "{} {}".format(TOOL_NAME, _addon_version()),
            re.sub(r"\s*\(.*\)", "", _t("source_cards" if render_mode == 1 else "source_fields")),
            _t("layout_compact" if compact else "layout_standard"),
        ])
        generator_css = (
            "@bottom-right{{content:\"{g}\";font-family:{f};font-size:7px;color:{c};"
            "opacity:.75}}".format(g=generator.replace("\\", "").replace('"', "'"), f=font, c=t["mut"])
        )
        page_num_css = (
            "@bottom-center{{content:counter(page) ' / ' counter(pages);"
            "font-family:{f};font-size:9px;color:{c}}}".format(f=font, c=t["mut"])
            if page_numbers else ""
        )

        sanitise_css = (
            ".fv [style*='background']{background:transparent!important}"
            ".fv [style*='Background']{background:transparent!important}"
            ".fv [bgcolor]{background:transparent!important}"
            ".fv .nightMode,.fv .night_mode,.fv .nightmode{all:unset!important}"
            ".fv [style*='color:white']{color:inherit!important}"
            ".fv [style*='color:#fff']{color:inherit!important}"
            ".fv [style*='color: white']{color:inherit!important}"
            ".fv [style*='width'][style*='height']{max-width:100%!important;height:auto!important}"
            ".fv style{display:none!important}"
            ".rs [style*='background']{background:transparent!important}"
            ".rs [bgcolor]{background:transparent!important}"
            ".rs .nightMode,.rs .night_mode,.rs .nightmode{all:unset!important}"
            ".rs [style*='color:white']{color:inherit!important}"
            ".rs [style*='color:#fff']{color:inherit!important}"
        )

        io_max_h = int(max(200, (page_h_px - top_mg_px * 2) * 0.62))
        cz_color = ["#2563eb", "#60a5fa", "#1d4ed8"][theme_idx if 0 <= theme_idx < 3 else 0]
        link = ["#1d63d8", "#7fb3ff", "#1d4ed8"][theme_idx if 0 <= theme_idx < 3 else 0]
        link_line = ["rgba(29,99,216,.35)", "rgba(127,179,255,.4)", "rgba(29,78,216,.35)"][
            theme_idx if 0 <= theme_idx < 3 else 0]
        io_css_str = (
            ".io-wrap{position:relative;display:inline-block;line-height:0;max-width:100%}"
            ".io-wrap img{display:block;max-width:100%!important;height:auto!important;"
            "width:auto!important;max-height:" + str(io_max_h) + "px!important;border-radius:0;margin:0}"
            ".io-wrap svg{position:absolute;top:0;left:0;margin:0!important;"
            "width:100%!important;height:100%!important}"
            ".rs .io-m{display:block;position:absolute;background:#ffeba2;border:1.5px solid #212121;"
            "box-sizing:border-box}"
            ".rs .io-o{display:block;position:absolute;border:2px dashed #e0482c;box-sizing:border-box}"
            ".rs .io-e{border-radius:50%}"
            ".rs .io-n{position:absolute;background:#e0482c;color:#fff!important;"
            "font-size:10px;font-weight:700;line-height:1;padding:2px 4px;border-radius:3px}"
            ".io-poly.io-m polygon{fill:#ffeba2;stroke:#212121;stroke-width:.006}"
            ".io-poly.io-o polygon{fill:none;stroke:#e0482c;stroke-width:.008;"
            "stroke-dasharray:.03 .02}"
            ".cz-a{font-weight:700;color:" + cz_color + ";border-bottom:1.5px solid " + cz_color + "}"
            ".cz-h{display:inline-block;min-width:3.2em;text-align:center;font-weight:700;"
            "color:" + cz_color + ";border-bottom:1.5px solid " + cz_color + ";line-height:1.1}"
            ".key-title{text-align:center;font-size:" + str(bsz + 6) + "px;font-weight:800;"
            "color:" + t["acc"] + ";margin:8px 0 12px;letter-spacing:-.02em}"
        )
        if high_contrast:
            _c = t["txt"]
            hc_css_str = (
                ".fv *{color:" + _c + "!important;background:transparent!important;"
                "background-color:transparent!important}"
                ".rs *{color:" + _c + "!important;background:transparent!important;"
                "background-color:transparent!important}"
            )
        else:
            hc_css_str = ""

        if compact:
            c_padh = max(3, padh * 2 // 3)
            c_padx = max(5, (pad + 2) * 2 // 3)
            compact_css = (
                "body.compact .card{{box-shadow:none;border-radius:4px}}"
                "body.compact .fb{{padding:{cph}px {cpx}px}}"
                "body.compact .rs{{padding:{cph}px {cpx}px}}"
                "body.compact .cnum{{padding:3px {cpx}px 1px}}"
                "body.compact .fv p{{margin:0 0 .1em}}"
                "body.compact .fv ul,body.compact .fv ol{{margin:.1em 0}}"
                "body.compact .fv li{{margin-bottom:0}}"
                "body.compact img{{margin:2px 0}}"
            ).format(cph=c_padh, cpx=c_padx)
        else:
            compact_css = ""

        footer_max_w_css = "{}px".format(card_max_w) if card_max_w > 0 else "640px"
        footer_margin = max(14, min_gap * 2)
        footer_pad = max(8, padh)
        footer_sz = max(9, bsz - 2)
        top_notice_sz = max(8, bsz - 3)
        top_notice_gap = max(16, min_gap * 2)

        content_css = (
            "{font_import}"
            "*,*::before,*::after{{font-family:{font}!important;box-sizing:border-box!important;"
            "-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}}"
            "html{{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}}"
            "body{{color:{txt};font-size:{bsz}px;line-height:{lh};"
            "-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;"
            "word-wrap:break-word;overflow-wrap:break-word;"
            "-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}}"
            "h1.doc-title{{text-align:center;font-size:{h1sz}px;font-weight:800;"
            "color:{acc};margin:12px 0 {titlegap}px;padding-top:8px;letter-spacing:-.03em}}"
            ".sub{{text-align:center;color:{mut};font-size:{subsz}px;"
            "font-weight:500;margin:0 0 {subgap}px;letter-spacing:-.01em}}"
            ".card{{{card_extra}background:{card};margin-bottom:{gap}px!important;"
            "break-inside:avoid;page-break-inside:avoid;display:flow-root;width:100%;"
            "box-decoration-break:clone;-webkit-box-decoration-break:clone}}"
            # cards the layout pass allows to continue on the next page (never inside a field)
            ".card.long-card,.card.split-ok{{break-inside:auto;page-break-inside:auto}}"
            ".card.long-card .sec-q,.card.long-card .sec-a,.card.long-card .sec-x,"
            ".card.split-ok .sec-q,.card.split-ok .sec-a,.card.split-ok .sec-x{{"
            "break-inside:auto;page-break-inside:auto}}"
            ".cnum{{font-size:9px;font-weight:700;color:{mut};"
            "text-transform:uppercase;letter-spacing:.1em;padding:6px {padx}px 2px}}"
            ".sec-q,.sec-a,.sec-x{{display:block}}"
            # a card never ends a page with only its header: number, question, divider and the
            # field label all stay with what follows them
            ".cnum,.sec-q,.sec-div,.fl{{break-after:avoid;page-break-after:avoid}}"
            ".sec-div{{height:0;border:none;border-top:1px solid {div};margin:0}}"
            ".fb{{padding:{padh}px {padx}px;break-inside:avoid;page-break-inside:avoid}}"
            ".fb.fb-long{{break-inside:auto;page-break-inside:auto}}"
            ".fb+.fb{{border-top:1px solid {div}}}"
            ".fl{{font-size:{flsz}px;font-weight:600;color:{mut};"
            "text-transform:uppercase;letter-spacing:.06em;margin-bottom:1px}}"
            ".fv{{font-size:inherit;orphans:2;widows:2}}"
            ".fv *{{max-width:100%!important}}"
            ".fv p{{margin:0 0 .2em}}.fv p:last-child{{margin:0}}"
            ".fv ul,.fv ol{{margin:.15em 0;padding-left:1.3em}}"
            ".fv li{{margin-bottom:.05em}}"
            ".fv table{{border-collapse:collapse;width:100%;margin:.2em 0}}"
            ".fv td,.fv th{{border:1px solid {brd};padding:3px 5px;font-size:.9em}}"
            ".fv h1{{font-size:1.1em;text-align:left;margin:0 0 .2em;letter-spacing:normal;"
            "padding:0;font-weight:700}}"
            ".fv h2{{font-size:1.05em;margin:0 0 .2em;font-weight:700}}"
            ".fv h3{{font-size:1em;margin:0 0 .15em;font-weight:600}}"
            ".fv a,.rs a{{color:{link};text-decoration:none;border-bottom:1px solid {link_line}}}"
            ".fv details,.rs details{{display:block;margin:.1em 0}}"
            ".fv summary,.rs summary{{display:block;list-style:none;font-size:.8em;font-weight:600;"
            "color:{mut};letter-spacing:.02em;margin:0 0 .15em}}"
            ".fv summary::-webkit-details-marker,.rs summary::-webkit-details-marker{{display:none}}"
            "img{{max-width:100%!important;max-height:{img_h}px;width:auto!important;"
            "height:auto!important;"
            "object-fit:contain;margin:3px 0;border-radius:4px;display:inline-block;"
            "vertical-align:top;break-inside:avoid;page-break-inside:avoid}}"
            ".fv table,.rs table{{table-layout:fixed}}"
            ".fv td img,.fv th img{{max-width:100%!important}}"
            ".io-wrap{{break-inside:avoid;page-break-inside:avoid}}"
            "svg{{max-width:100%!important;height:auto!important;display:block;margin:3px 0}}"
            ".fv img:only-child{{margin:2px 0}}"
            "p:empty{{display:none}}div:empty{{display:none}}"
            ".rs{{padding:{padh}px {padx}px}}"
            ".rs *{{max-width:100%!important}}"
            ".rs .label{{font-size:{flsz}px;font-weight:600;color:{mut};"
            "text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px}}"
            ".nightMode,.night_mode{{all:unset!important}}"
            ".export-topnotice{{margin:0 auto {top_notice_gap}px;color:{mut};"
            "font-size:{top_notice_sz}px;line-height:1.25;text-align:center;"
            "max-width:{footer_max_w};width:100%;overflow-wrap:anywhere}}"
            ".export-topnotice a{{color:{mut};text-decoration:none;font-weight:600}}"
            ".export-footer{{margin:{footer_margin}px auto 0;padding:{footer_pad}px 0 0;"
            "border-top:1px solid {brd};color:{mut};font-size:{footer_sz}px;"
            "line-height:1.35;text-align:center;break-inside:avoid;page-break-inside:avoid;"
            "max-width:{footer_max_w};width:100%;overflow-wrap:anywhere}}"
            ".export-footer a{{color:{acc};text-decoration:none;font-weight:600}}"
            "{content_max_w}"
            "{sanitise}"
            "{compact_overrides}"
            "{io_css}"
            "{hc_css}"
        ).format(
            font_import=font_import, font=font, txt=t["txt"], bsz=bsz, lh=lh,
            h1sz=bsz + 8, acc=t["acc"], mut=t["mut"], titlegap=title_gap,
            subsz=bsz - 2, subgap=min_gap + 2,
            card_extra=card_extra, card=t["card"], gap=css_gap,
            pad=pad, padh=padh, padx=pad + 2, link=link, link_line=link_line,
            div=t["div"], flsz=label_sz, brd=t["brd"], img_h=img_h,
            footer_margin=footer_margin, footer_pad=footer_pad,
            footer_sz=footer_sz, footer_max_w=footer_max_w_css,
            top_notice_sz=top_notice_sz, top_notice_gap=top_notice_gap,
            content_max_w=content_max_w_css,
            sanitise=sanitise_css,
            compact_overrides=compact_css,
            io_css=io_css_str,
            hc_css=hc_css_str,
        )

        if mode == "pdf":
            wrapper_css = (
                "@page{{size:{ps};margin:{top_mm:.2f}mm {mg_mm:.2f}mm {bot_mm:.2f}mm {mg_mm:.2f}mm;"
                "background:{bg};{pnum}{gen}}}"
                "{content}"
                "html{{background-color:{bg}!important;min-height:100%;"
                "-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}}"
                "body{{background-color:{bg}!important;margin:0;padding:0;"
                "-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}}"
                ".pdf-bg{{position:fixed;top:0;left:0;right:0;bottom:0;background:{bg};"
                "z-index:0;-webkit-print-color-adjust:exact!important;"
                "print-color-adjust:exact!important}}"
                "div.page-break{{display:block!important;height:0;margin:0;padding:0;"
                "break-before:page;page-break-before:always}}"
                ".page-content{{position:relative;z-index:1;display:flow-root}}"
                "h1.doc-title{{margin-top:0}}"
            ).format(ps=ps, content=content_css, bg=t["body"],
                     top_mm=top_mg, mg_mm=mg, bot_mm=bottom_mm, pnum=page_num_css,
                     gen=generator_css)

        elif mode == "pdf_fallback":
            wrapper_css = (
                "@page{{size:{ps};margin:0}}"
                "{content}"
                "html{{background-color:{bg}!important;min-height:100%;"
                "-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}}"
                "body{{background-color:{bg}!important;margin:0;"
                "padding:{mg}mm;padding-top:0;"
                "-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}}"
                ".page-content{{position:relative;z-index:1}}"
            ).format(ps=ps, mg=mg, content=content_css, bg=t["body"])

        elif mode == "preview":
            wrapper_css = (
                "{content}"
                "html,body{{margin:0;padding:0}}"
                "html{{background:#3f3f46}}"
                "body{{display:flex;flex-direction:column;align-items:center;"
                "padding:32px 0;min-height:100vh;background:#3f3f46}}"
                ".page{{position:relative;"
                "width:{pw:.0f}px;min-height:{ph:.0f}px;"
                "background:{bg};padding:{mg:.0f}px;"
                "box-shadow:0 4px 24px rgba(0,0,0,.35),0 0 0 1px rgba(0,0,0,.08);"
                "margin-bottom:6px}}"
                ".page-break-marker{{width:{pw:.0f}px;height:24px;"
                "display:flex;align-items:center;justify-content:center;"
                "margin-bottom:6px;position:relative}}"
                ".page-break-marker::before{{content:'';position:absolute;"
                "left:0;right:0;top:50%;border-top:1px dashed rgba(255,255,255,.25)}}"
                ".page-break-marker span{{position:relative;background:#3f3f46;"
                "color:rgba(255,255,255,.4);font-size:10px;font-weight:600;"
                "padding:0 10px;font-family:sans-serif;letter-spacing:.05em}}"
                "@media print{{"
                "@page{{size:{ps};margin:{mg_mm}mm}}"
                "html,body{{background:{bg};padding:0}}"
                ".page{{box-shadow:none;margin:0;width:100%;min-height:auto;padding:0}}"
                ".page-break-marker{{display:none}}"
                "}}"
            ).format(content=content_css, pw=page_w_px, ph=page_h_px,
                     mg=mg_px, mg_mm=mg, ps=ps, bg=t["body"])
        else:
            wrapper_css = (
                "{content}"
                "body{{background:{bg};margin:0;padding:0}}"
                ".page-content{{padding:20px 24px}}"
                "body.grid-mode .page-content{{display:grid;"
                "grid-template-columns:repeat(auto-fill,minmax(340px,1fr));"
                "gap:{gap}px;align-items:start;"
                "max-width:none!important;width:100%}}"
                "body.grid-mode .page-content h1.doc-title,"
                "body.grid-mode .page-content .sub{{grid-column:1/-1}}"
                "body.grid-mode .card{{margin-bottom:0!important}}"
                "#lbx{{display:flex;position:fixed;inset:0;z-index:9999;"
                "background:rgba(0,0,0,.93);align-items:center;"
                "justify-content:center;overflow:hidden;"
                "opacity:0;pointer-events:none;"
                "transition:opacity .18s ease}}"
                "#lbx.open{{opacity:1;pointer-events:auto}}"
                "#lbx-img{{width:auto;height:auto;"
                "max-width:none!important;max-height:none!important;"
                "cursor:grab;user-select:none;-webkit-user-drag:none;"
                "touch-action:none;"
                "will-change:transform;border-radius:3px;"
                "transition:transform .1s cubic-bezier(.25,.46,.45,.94)}}"
                "#lbx-img.dragging{{cursor:grabbing;transition:none}}"
                "#lbx-img.no-anim{{transition:none}}"
                "#lbx-close{{position:fixed;top:14px;right:18px;"
                "width:34px;height:34px;"
                "background:rgba(255,255,255,.12);"
                "border:1px solid rgba(255,255,255,.2);border-radius:50%;"
                "color:#fff;font-size:17px;line-height:1;"
                "cursor:pointer;display:flex;align-items:center;"
                "justify-content:center;transition:background .15s;"
                "z-index:10001;font-family:system-ui,sans-serif;"
                "padding:0}}"
                "#lbx-close:hover{{background:rgba(255,255,255,.26)}}"
                ".page-content img{{cursor:zoom-in!important}}"
            ).format(
                content=content_css, bg=t["body"], gap=css_gap,
            )

        body_classes = []
        if compact:
            body_classes.append("compact")
        if grid_mode:
            body_classes.append("grid-mode")
        body_classes.append(THEME_CLASS_NAMES[theme_idx] if 0 <= theme_idx < len(THEME_CLASS_NAMES) else THEME_CLASS_NAMES[0])
        body_cls = ' class="{}"'.format(" ".join(body_classes)) if body_classes else ''
        show_tool_notice = mode in ("pdf", "pdf_fallback", "preview")

        def build_tool_top_notice():
            top_label = _t("pdf_top_tool_notice").format(
                tool=TOOL_NAME,
                url=TOOL_URL_DISPLAY,
            )
            return (
                '<div class="export-topnotice">'
                '<a href="{}">{}</a>'
                '</div>'
            ).format(
                html_module.escape(TOOL_URL),
                html_module.escape(top_label),
            )

        if mode == "pdf":
            _bg = t["body"]
            html_open = (
                '<!DOCTYPE html>'
                '<html style="background-color:{bg};margin:0;padding:0;'
                '-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important">'
                '<head><meta charset="utf-8"><style>'
            ).format(bg=_bg)
            body_open = (
                '</style></head>'
                '<body{cls} style="background-color:{bg};margin:0;padding:0;'
                '-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important">'
                '<div class="pdf-bg"></div>'
            ).format(cls=body_cls, bg=_bg)
            html = [html_open, wrapper_css, body_open]
        elif mode == "pdf_fallback":
            _bg = t["body"]
            html_open = (
                '<!DOCTYPE html>'
                '<html style="background-color:{bg};margin:0;padding:0;'
                '-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important">'
                '<head><meta charset="utf-8"><style>'
            ).format(bg=_bg)
            body_open = (
                '</style></head>'
                '<body{cls} style="background-color:{bg};margin:0;'
                'padding:{mg}mm;padding-top:0;'
                '-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important">'
                '<div style="position:fixed;top:0;left:0;right:0;bottom:0;'
                'background-color:{bg};z-index:0;'
                '-webkit-print-color-adjust:exact!important;'
                'print-color-adjust:exact!important"></div>'
            ).format(cls=body_cls, bg=_bg, mg=mg)
            html = [html_open, wrapper_css, body_open]
        else:
            html = [
                "<!DOCTYPE html><html><head><meta charset='utf-8'><style>",
                wrapper_css,
                "</style></head><body{}>".format(body_cls),
            ]

        if mode == "preview":
            html.append('<div class="page"><div class="page-content">')
        else:
            html.append('<div class="page-content">')
        html.append('<!-- {} -->'.format(EXPORT_BUILD))
        if show_tool_notice and not show_title:
            html.append(build_tool_top_notice())

        if show_title:
            html.append('<h1 class="doc-title">{}</h1>'.format(
                html_module.escape(display_title)))
            html.append('<div class="sub">{} {}</div>'.format(
                html_module.escape(_t("deck_lbl")),
                html_module.escape(deck_path)))
            if show_tool_notice:
                html.append(build_tool_top_notice())

        card_ids = self._find_card_ids(deck_name)
        logger.log("Kart: {}".format(len(card_ids)))

        img_ok = [0]
        img_fail = [0]

        def b64(fn):
            clean = urllib.parse.unquote(fn)
            clean = clean.split('?')[0].split('#')[0]
            p = os.path.join(media_dir, clean)
            if not os.path.exists(p):
                img_fail[0] += 1
                return None
            mt, _ = mimetypes.guess_type(p)
            try:
                with open(p, "rb") as fh:
                    data = base64.b64encode(fh.read()).decode()
                img_ok[0] += 1
                return "data:{};base64,{}".format(mt or "image/jpeg", data)
            except Exception:
                img_fail[0] += 1
                return None

        def fix_img(m):
            d = b64(m.group(2))
            return "src={}{}{}".format(m.group(1), d, m.group(1)) if d else m.group(0)

        img_re = re.compile(r'src=(["\'])(?!http|data:)([^"\']+)\1', re.IGNORECASE)
        xlink_re = re.compile(r'xlink:href=(["\'])(?!http|data:)([^"\']+)\1', re.IGNORECASE)

        def fix_xlink(m):
            d = b64(m.group(2))
            return "xlink:href={}{}{}".format(m.group(1), d, m.group(1)) if d else m.group(0)

        def proc_media(text):
            if not text:
                return ""
            text = img_re.sub(fix_img, text)
            text = xlink_re.sub(fix_xlink, text)
            return text

        def _protect_svg(raw):
            svgs = []
            def _save(m):
                svgs.append(m.group(0))
                return "<!--SVG_PROTECT_{}-->".format(len(svgs) - 1)
            raw = re.sub(r'<svg\b[^>]*>.*?</svg>', _save, raw,
                         flags=re.DOTALL | re.IGNORECASE)
            return raw, svgs

        def _restore_svg(raw, svgs):
            for i, svg in enumerate(svgs):
                raw = raw.replace("<!--SVG_PROTECT_{}-->".format(i), svg)
            return raw

        def _normalize_block_spacing(raw):
            if not raw:
                return raw
            raw = re.sub(r'(<br\s*/?>\s*){3,}', '<br><br>', raw, flags=re.IGNORECASE)
            raw = re.sub(
                r'(?:<(?:div|p)>\s*(?:&nbsp;|\s|<br\s*/?>)*</(?:div|p)>\s*){3,}',
                '<div><br></div>',
                raw,
                flags=re.IGNORECASE,
            )
            return raw.strip()

        def sanitise_html(raw):
            if not raw:
                return raw
            raw = _MEDIA_TAG_RE.sub("", raw)
            raw, svgs = _protect_svg(raw)
            raw = re.sub(r"<style[^>]*>.*?</style>", "", raw, flags=re.DOTALL | re.IGNORECASE)
            raw = re.sub(r"<script[^>]*>.*?</script>", "", raw, flags=re.DOTALL | re.IGNORECASE)
            raw = re.sub(r"<meta[^>]*>", "", raw, flags=re.IGNORECASE)
            # collapsed <details> would hide their content on paper (Chromium honours "closed")
            raw = re.sub(r"<details\b(?![^>]*\bopen\b)", "<details open", raw, flags=re.IGNORECASE)
            raw = re.sub(r"<title[^>]*>.*?</title>", "", raw, flags=re.DOTALL | re.IGNORECASE)
            raw = re.sub(r"<h1[^>]*>(.*?)</h1>", r"<p><strong>\1</strong></p>",
                         raw, flags=re.DOTALL | re.IGNORECASE)
            raw = re.sub(r"<h2[^>]*>(.*?)</h2>", r"<p><strong>\1</strong></p>",
                         raw, flags=re.DOTALL | re.IGNORECASE)
            raw = re.sub(r"\sbgcolor=(['\"]).*?\1", "", raw, flags=re.IGNORECASE | re.DOTALL)

            def _clean_style_attr(match):
                quote = match.group(1)
                style = match.group(2)
                style = re.sub(
                    r'(?i)(?:^|;)\s*background(?:-color|-image)?\s*:[^;]+;?',
                    ';',
                    style,
                )
                style = re.sub(
                    r'(?i)(?:^|;)\s*color\s*:\s*(?:white|#fff(?:fff)?|rgb\(\s*255\s*,\s*255\s*,\s*255\s*\))\s*;?',
                    ';',
                    style,
                )
                style = re.sub(r'\s+', ' ', style)
                style = re.sub(r';{2,}', ';', style).strip(' ;')
                return ' style={}{}{}'.format(quote, style, quote) if style else ''

            raw = re.sub(
                r'\sstyle=(["\'])(.*?)\1',
                _clean_style_attr,
                raw,
                flags=re.IGNORECASE | re.DOTALL,
            )
            raw = re.sub(
                r'width:\s*(\d{4,})px',
                lambda m: "width:100%" if int(m.group(1)) > 800 else m.group(0), raw)
            raw = _normalize_block_spacing(raw)
            return _restore_svg(raw, svgs)

        def proc_raw(raw):
            if not raw or raw in ("<br>", "<div><br></div>", "&nbsp;"):
                return ""
            raw = sanitise_html(raw)
            if strip:
                # drop formatting but keep the line structure (paragraphs, lists, line breaks)
                raw = re.sub(r"(?i)<br\s*/?>|</(?:p|div|li|tr|h[1-6]|summary|details|ul|ol|table)>",
                             "\n", raw)
                raw = re.sub(r"(?i)<li\b[^>]*>", "\n\u2022 ", raw)
                raw = re.sub(r"<(?!img\b|svg|/svg)[^>]+>", " ", raw)
                raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
                raw = re.sub(r" ?\n ?", "\n", raw)
                raw = re.sub(r"\n{3,}", "\n\n", raw).strip()
                raw = raw.replace("\n", "<br>")
            return proc_media(raw)

        def fstyle(c):
            p = ["font-size:{};".format(sz_map[c["size"]])]
            if c["bg"] != 0:
                p.append("background:{};".format(bg_map[c["bg"]]))
            if c["color"]:
                p.append("color:{};".format(cl_map[c["color"]]))
            p.append("text-align:{};".format(al_map[c["align"]]))
            if c["bold"]:
                p.append("font-weight:700;")
            if c["italic"]:
                p.append("font-style:italic;")
            if c["underline"]:
                p.append("text-decoration:underline;")
            return "".join(p)

        def render_field(fname, val, conf):
            if not val:
                return ""
            label = '<div class="fl">{}</div>'.format(html_module.escape(fname)) if conf["label"] else ""
            chars, lines = _text_metrics(val)
            long_field = chars > 900 or lines > 14 or val.count("<img") > 2
            return '<div class="fb{}" style="{}"><div class="fv">{}{}</div></div>'.format(
                " fb-long" if long_field else "", fstyle(conf), label, val)

        def clean_rendered(raw_html):
            raw_html, svgs = _protect_svg(raw_html)
            c = re.sub(r"<style[^>]*>.*?</style>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
            c = re.sub(r"<script[^>]*>.*?</script>", "", c, flags=re.DOTALL | re.IGNORECASE)
            c = sanitise_html(c.strip())
            return _restore_svg(c, svgs)

        # ---- FIX: improved page height calculations ----
        content_h_px = page_h_px - top_mg_px - top_mg_px  # top + bottom margin
        break_h_px = content_h_px

        top_notice_h_est = int(top_notice_sz * 1.25 + top_notice_gap) if show_tool_notice else 0
        if show_title:
            _title_h = int((bsz + 8) * lh + 8 + title_gap)
            _sub_h = int((bsz - 2) * lh + min_gap + 2)
            title_h_est = top_notice_h_est + _title_h + _sub_h
        else:
            title_h_est = top_notice_h_est
        accumulated_h = [title_h_est]
        cards_on_page = [0]

        # ---- FIX: clean page breaks without spacer images ----
        def emit_page_break(use_margin=True):
            accumulated_h[0] = 0
            cards_on_page[0] = 0
            if mode == "preview":
                return (
                    '</div></div>'
                    '<div class="page-break-marker">'
                    '<span>' + _t("page_break_lbl") + '</span></div>'
                    '<div class="page"><div class="page-content">'
                )
            if mode == "pdf_fallback":
                h = int(top_mg_px) if use_margin else 0
                return '<div style="break-before:page;height:{}px;display:block;margin:0;padding:0"></div>'.format(h)
            return '<div class="page-break"></div>'

        def build_tool_footer():
            footer_label = _t("pdf_footer_generated").format(
                tool=TOOL_NAME,
                version=_addon_version() + (
                    " \u00b7 " + " \u00b7 ".join(generator.split(" \u00b7 ")[1:]) if mode != "pdf" else ""),
            )
            return (
                '<footer class="export-footer">'
                '{} &middot; <a href="{}">{}</a>'
                '</footer>'
            ).format(
                html_module.escape(footer_label),
                html_module.escape(TOOL_URL),
                html_module.escape(TOOL_URL_DISPLAY),
            )

        def _text_metrics(html_str):
            text = html_str or ""
            text = re.sub(r"(?i)<br\s*/?>", "\n", text)
            text = re.sub(r"(?i)</(p|div|li|tr|h[1-6])>", "\n", text)
            text = re.sub(r"<[^>]+>", " ", text)
            lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
            hard_lines = sum(1 for line in lines if line)
            return sum(len(line) for line in lines), hard_lines

        # ---- FIX: improved card height estimation ----
        def estimate_card_h(sections_count, has_image, text_chars=0, n_images=1, hard_lines=0,
                            img_px=None):
            overhead = (20 if show_nums else 0) + sections_count * (padh * 2 + 2) + max(0, sections_count - 1)
            effective_w = card_max_w if card_max_w > 0 else (pw_mm * ppm - 2 * mg_px)
            cpp = max(10, int((effective_w - pad * 2) / (bsz * 0.6)))
            if text_chars > 0:
                n_lines = max(sections_count, hard_lines, (text_chars + cpp - 1) // cpp)
            else:
                n_lines = sections_count * 2
            text_h = n_lines * bsz * lh
            img_est = min(n_images, 5) * (img_px or min(img_h, 200)) if has_image else 0
            return int(overhead + text_h + img_est + 4)

        def card_class(est):
            # PDF: the WeasyPrint layout pass measures real gaps and decides which cards may
            # continue on the next page; only cards certainly taller than a page start split.
            if mode == "pdf" and est > break_h_px * 0.95:
                return "card long-card"
            return "card"

        unit_seq = [0]

        # ------------------------------------------------------------ entries
        qa_layout = self.qa_combo.currentIndex()
        cloze_mode = self.cloze_combo.currentIndex()   # 0 reveal 1 hide 2 both 3 native
        io_each = self.io_combo.currentIndex() == 1
        cards_style = render_mode == 1
        show_cnum = show_nums or qa_layout != 0
        io_img_est = int(min(io_max_h, 320))

        entries = []
        seen = set()
        cards_ok = 0
        cards_skip = 0
        model_cache = {}

        def get_model(note):
            nt = model_cache.get(note.mid)
            if nt is None:
                nt = mw.col.models.get(note.mid)
                model_cache[note.mid] = nt
            return nt

        def est_html(markup, img_px=None):
            sec_count = max(1, len(re.findall(r'class="sec-[qax]"', markup)))
            chars, lines = _text_metrics(markup)
            n_imgs = markup.count("<img")
            return estimate_card_h(sec_count, n_imgs > 0, chars, max(1, n_imgs), lines, img_px)

        def rs_section(css, label_key, body):
            return ('<div class="{}"><div class="rs"><div class="label">{}</div>{}</div></div>'
                    .format(css, html_module.escape(_t(label_key)), body))

        def add_entry(nt_name, q_html, a_html, img_px=None):
            if not q_html and not a_html:
                return False
            num = len(entries) + 1
            both = q_html + a_html
            entries.append({
                "num": num, "nt": nt_name, "q": q_html, "a": a_html,
                "est": est_html(both, img_px),
                "est_q": est_html(q_html, img_px) if q_html else 0,
                "est_a": est_html(a_html, img_px) if a_html else 0,
                "alt": ' style="background:{}"'.format(t["alt"]) if zebra and num % 2 == 0 else "",
            })
            return True

        def io_entry(io, active_ord):
            """Question: masks over the image. Answer: the image with the masks outlined."""
            shapes = io["shapes"]
            if active_ord is None:                    # all masks at once
                q_masks, a_masks, a_marks = shapes, [], shapes
            else:                                     # one card per mask, as Anki does it
                active = [sh for sh in shapes if sh["ord"] == active_ord]
                inactive = [sh for sh in shapes if sh["ord"] != active_ord]
                hide_rest = any(sh["oi"] for sh in shapes)
                q_masks = active + (inactive if hide_rest else [])
                a_masks = inactive if hide_rest else []
                a_marks = active
            header = proc_media(proc_raw(io["rest"][0][1])) if io["rest"] else ""
            extras = "".join(
                '<div class="fv">{}</div>'.format(proc_media(proc_raw(v))) for _, v in io["rest"])
            image = proc_media(io["image"])
            q = rs_section("sec-q", "rendered_front",
                           (('<div class="fv">{}</div>'.format(header)) if header else "")
                           + _io_figure(image, masks=q_masks))
            a = rs_section("sec-a", "rendered_back",
                           _io_figure(image, masks=a_masks, outlines=a_marks) + extras)
            return q, a

        def cloze_entry(fields_by_name, nt, czm):
            """One entry per cloze note: hidden/revealed text plus the other fields."""
            main, extras = [], []
            for fld in sorted(nt["flds"], key=lambda f: f["ord"]):
                val = fields_by_name.get(fld["name"], "")
                if not val.strip():
                    continue
                if "{{c" in val:
                    main.append(val)
                else:
                    extras.append(val)
            if not main:
                return None
            def body(parts, reveal):
                return "".join('<div class="fv">{}</div>'.format(
                    proc_media(clean_rendered(_cloze_render(v, reveal)))) for v in parts)
            extra_html = "".join('<div class="fv">{}</div>'.format(
                proc_media(clean_rendered(v))) for v in extras)
            if czm == 0:       # reveal
                return rs_section("sec-q", "rendered_front", body(main, True)), \
                    (rs_section("sec-a", "rendered_back", extra_html) if extra_html else "")
            if czm == 1:       # hide
                return rs_section("sec-q", "rendered_front", body(main, False)), \
                    (rs_section("sec-a", "rendered_back", extra_html) if extra_html else "")
            return rs_section("sec-q", "rendered_front", body(main, False)), \
                rs_section("sec-a", "rendered_back", body(main, True) + extra_html)

        def native_entry(card, note, nt):
            q = proc_media(clean_rendered(card.question()))
            answer = card.answer()
            pieces = _ANSWER_HR_RE.split(answer, maxsplit=1)
            if len(pieces) == 2 and pieces[1].strip():
                answer = pieces[1]          # drop the repeated question above <hr id=answer>
            a = proc_media(clean_rendered(answer))
            if "image occlusion" in nt["name"].lower():
                q = '<div class="io-wrap">{}</div>'.format(q) if q else q
                a = '<div class="io-wrap">{}</div>'.format(a) if a else a
            return (rs_section("sec-q", "rendered_front", q) if q else "",
                    rs_section("sec-a", "rendered_back", a) if a else "")

        def fields_entry(fields_by_name, nt, fc_nt):
            czm = cloze_mode if cloze_mode != 3 else 0
            sq, sa, sx, revealed_copies = [], [], [], []
            for fld in sorted(nt["flds"], key=lambda f: f["ord"]):
                fname = fld["name"]
                conf = fc_nt.get(fname) or _auto_field_config(fname)
                if not conf["export"]:
                    continue
                raw_val = fields_by_name.get(fname, "")
                if not raw_val.strip():
                    continue
                text = raw_val.strip()
                section = conf["section"]
                if nt["type"] == 1 and "{{c" in text:
                    if czm == 0:
                        text = _cloze_render(text, True)
                    elif czm == 1:
                        text = _cloze_render(text, False)
                    elif section == 0:
                        revealed_copies.append((fname, conf, _cloze_render(text, True)))
                        text = _cloze_render(text, False)
                    else:
                        text = _cloze_render(text, True)
                val = proc_raw(text)
                if not val:
                    continue
                target = (sq, sa, sx)[section]
                target.append(render_field(fname, val, conf))
            for fname, conf, text in reversed(revealed_copies):
                val = proc_raw(text)
                if val:
                    sa.insert(0, render_field(fname, val, conf))
            q_html = '<div class="sec-q">{}</div>'.format("".join(sq)) if sq else ""
            a_html = ""
            if sa:
                a_html += '<div class="sec-a">{}</div>'.format("".join(sa))
            if sx:
                a_html += ('<hr class="sec-div">' if sa else "") + \
                    '<div class="sec-x">{}</div>'.format("".join(sx))
            return q_html, a_html

        fc = self._collect_fc()
        for cid in card_ids:
            try:
                card = mw.col.get_card(cid)
                note = card.note()
                nt = get_model(note)
                fields_by_name = {f["name"]: note.fields[f["ord"]]
                                  for f in nt["flds"] if f["ord"] < len(note.fields)}
                io = _parse_io(fields_by_name, nt) if nt["type"] == 1 else None
                if io:
                    key = (note.id, card.ord) if io_each else (note.id,)
                    if key in seen:
                        continue
                    seen.add(key)
                    q_html, a_html = io_entry(io, card.ord + 1 if io_each else None)
                    img_px = io_img_est
                elif cards_style and not (nt["type"] == 1 and cloze_mode != 3):
                    q_html, a_html = native_entry(card, note, nt)
                    img_px = None
                else:
                    if note.id in seen:
                        continue
                    seen.add(note.id)
                    if cards_style:
                        pair = cloze_entry(fields_by_name, nt, cloze_mode)
                        q_html, a_html = pair if pair else ("", "")
                    else:
                        q_html, a_html = fields_entry(fields_by_name, nt, fc.get(nt["id"], {}))
                    img_px = None
                if add_entry(nt["name"], q_html, a_html, img_px):
                    cards_ok += 1
                else:
                    cards_skip += 1
            except Exception as e:
                logger.error("Karta #{}".format(cid), e)
                cards_skip += 1

        # ------------------------------------------------- layout -> units
        def make_unit(ent, which):
            if which == "both":
                inner = ent["q"] + ('<hr class="sec-div">' if ent["q"] and ent["a"] else "") + ent["a"]
                est = ent["est"]
            elif which == "q":
                inner, est = ent["q"], ent["est_q"]
            else:
                inner, est = ent["a"], ent["est_a"]
            unit_seq[0] += 1
            parts = ['<div class="{}"{} data-u="{}">'.format(card_class(est), ent["alt"], unit_seq[0])]
            if show_cnum:
                label = "#{}".format(ent["num"])
                if which == "a":
                    label += " &middot; " + html_module.escape(_t("lbl_answer"))
                elif cards_style:
                    label += " &middot; " + html_module.escape(ent["nt"])
                parts.append('<div class="cnum">{}</div>'.format(label))
            parts.append(inner)
            parts.append("</div>")
            return {"est": est, "parts": parts, "brk": False}

        units = []
        if qa_layout == 1:                        # worksheet, then answer key
            units.extend(make_unit(e, "q") for e in entries if e["q"])
            key_started = False
            for e in entries:
                if not e["a"]:
                    continue
                u = make_unit(e, "a")
                if not key_started:
                    u["parts"].insert(0, '<h2 class="key-title">{}</h2>'.format(
                        html_module.escape(_t("answers_title"))))
                    u["est"] += 48
                    u["brk"] = bool(units)
                    key_started = True
                units.append(u)
        elif qa_layout == 2:                      # question page, then answer page, per entry
            for e in entries:
                for which in ("q", "a"):
                    if e[which]:
                        u = make_unit(e, which)
                        u["brk"] = bool(units)
                        units.append(u)
        else:
            units = [make_unit(e, "both") for e in entries]

        # ---------------------------------------------------- placement
        def pack_units(segment, start_h):
            pages, current, used = [], [], start_h
            for u in segment:
                needed = u["est"] + (card_gap if current else 0)
                if current and used + needed > break_h_px:
                    pages.append(current)
                    current, used = [u], u["est"]
                else:
                    current.append(u)
                    used += needed
            if current:
                pages.append(current)
            return pages

        if mode == "pdf":
            for n, u in enumerate(units):
                parts = u["parts"]
                if u["brk"] and n:
                    html.append('<div class="page-break"></div>')
                    # a forced break is intended: the layout pass must not fill the gap before it
                    parts = [p.replace(' data-u="', ' data-keep="1" data-u="', 1)
                             if p.startswith('<div class="card') else p for p in parts]
                html.extend(parts)
            self._last_layout = {
                # largest empty part of a page (fraction) tolerated to keep a card in one piece
                "gap_ratio": 0 if qa_layout == 2 else (0.12 if compact else 0.33),
                # ...but a card shorter than this (fraction of a page) always stays in one piece
                "min_split": 0.25 if compact else 0.4,
            }
        elif mode == "legacy":
            for u in units:
                html.extend(u["parts"])
        elif compact and mode == "preview":
            segments = [[]]
            for u in units:
                if u["brk"] and segments[-1]:
                    segments.append([])
                segments[-1].append(u)
            first_page = True
            for si, segment in enumerate(segments):
                for page_units in pack_units(segment, title_h_est if si == 0 else 0):
                    if not first_page:
                        html.append(emit_page_break())
                    first_page = False
                    for u in page_units:
                        html.extend(u["parts"])
        elif compact:                              # pdf_fallback
            acc_h, on_page = title_h_est, 0
            for u in units:
                if on_page and (u["brk"] or acc_h + u["est"] > break_h_px):
                    html.append('<div style="break-before:page;height:0;'
                                'display:block;margin:0;padding:0"></div>')
                    acc_h, on_page = 0, 0
                acc_h += u["est"]
                on_page += 1
                html.extend(u["parts"])
        else:                                      # preview / pdf_fallback, standard layout
            for n, u in enumerate(units):
                needed = u["est"] + (card_gap if cards_on_page[0] > 0 else 0)
                overflow = accumulated_h[0] + needed > content_h_px and cards_on_page[0] > 0
                if (u["brk"] and n) or overflow:
                    html.append(emit_page_break(u["est"] <= page_h_px * 0.75))
                    needed = u["est"]
                accumulated_h[0] += needed
                cards_on_page[0] += 1
                html.extend(u["parts"])

        if show_tool_notice:
            html.append(build_tool_footer())

        if mode == "preview":
            html.append("</div></div>")
        else:
            html.append("</div>")

        if mode == "legacy":
            html.append(
                '<div id="lbx">'
                '<button id="lbx-close" title="' + _t("lbx_close_title") + '">&#x2715;</button>'
                '<img id="lbx-img" src="" alt="">'
                '</div>'
            )
            html.append(
                "<script>(function(){"
                "var lbx=document.getElementById('lbx'),"
                "li=document.getElementById('lbx-img'),"
                "cb=document.getElementById('lbx-close'),"
                "pc=document.querySelector('.page-content');"
                "var sc=1,ox=0,oy=0,drag=false,sx=0,sy=0,fitScale=1;"
                "var lastClick=0,lastClickX=0,lastClickY=0,ignoreNativeDbl=false,suppressClickUntil=0,openTimer=0;"
                "function applyT(){"
                "li.style.transform='translate('+ox+'px,'+oy+'px) scale('+sc+')';"
                "}"
                "function fitToView(){"
                "var vw=window.innerWidth*0.9,vh=window.innerHeight*0.9;"
                "var nw=li.naturalWidth||li.width||vw;"
                "var nh=li.naturalHeight||li.height||vh;"
                "fitScale=Math.min(1,Math.min(vw/nw,vh/nh));"
                "sc=fitScale;ox=0;oy=0;"
                "li.classList.remove('no-anim');"
                "applyT();"
                "}"
                "function toggleZoomAt(cx,cy){"
                "if(Math.abs(sc-fitScale)<0.01){"
                "var rect=lbx.getBoundingClientRect();"
                "var mx=cx-rect.width/2-ox;"
                "var my=cy-rect.height/2-oy;"
                "var ds=1/sc;"
                "ox-=mx*(ds-1);oy-=my*(ds-1);sc=1;"
                "}else{sc=fitScale;ox=0;oy=0;}"
                "li.classList.remove('no-anim');applyT();"
                "}"
                "function isQuickRepeat(cx,cy){"
                "var now=Date.now();"
                "var dx=cx-lastClickX,dy=cy-lastClickY;"
                "var hit=lastClick&&now-lastClick<330&&(dx*dx+dy*dy)<64;"
                "lastClick=now;lastClickX=cx;lastClickY=cy;"
                "return hit;"
                "}"
                "function openImg(src,full,cx,cy){"
                "if(openTimer){clearTimeout(openTimer);openTimer=0;}"
                "sc=1;ox=0;oy=0;"
                "lastClick=0;ignoreNativeDbl=false;suppressClickUntil=0;"
                "li.classList.add('no-anim');"
                "li.style.transform='';"
                "li.onload=function(){fitToView();if(full)toggleZoomAt(cx||window.innerWidth/2,cy||window.innerHeight/2);};"
                "li.src=src;"
                "lbx.classList.add('open');"
                "document.body.style.overflow='hidden';"
                "if(li.complete&&li.naturalWidth){fitToView();if(full)toggleZoomAt(cx||window.innerWidth/2,cy||window.innerHeight/2);}"
                "}"
                "function closeViewer(){"
                "if(openTimer){clearTimeout(openTimer);openTimer=0;}"
                "lbx.classList.remove('open');"
                "li.src='';"
                "document.body.style.overflow='';"
                "}"
                "if(pc)pc.addEventListener('click',function(e){"
                "var t=e.target;"
                "while(t&&t!==pc){"
                "if(t.tagName==='IMG'){"
                "var src=t.src,cx=e.clientX,cy=e.clientY;"
                "if(openTimer)clearTimeout(openTimer);"
                "openTimer=setTimeout(function(){openImg(src,false,cx,cy);},180);return;}"
                "t=t.parentNode;}"
                "});"
                "if(pc)pc.addEventListener('dblclick',function(e){"
                "var t=e.target;"
                "while(t&&t!==pc){"
                "if(t.tagName==='IMG'){e.preventDefault();e.stopPropagation();"
                "if(openTimer){clearTimeout(openTimer);openTimer=0;}"
                "openImg(t.src,true,e.clientX,e.clientY);return;}"
                "t=t.parentNode;}"
                "});"
                "cb.addEventListener('click',closeViewer);"
                "lbx.addEventListener('click',function(e){"
                "if(e.target===lbx)closeViewer();"
                "});"
                "document.addEventListener('keydown',function(e){"
                "if(e.key==='Escape'&&lbx.classList.contains('open'))closeViewer();"
                "});"
                "li.addEventListener('wheel',function(e){"
                "e.preventDefault();"
                "var rect=lbx.getBoundingClientRect();"
                "var mx=e.clientX-rect.width/2-ox;"
                "var my=e.clientY-rect.height/2-oy;"
                "var factor=Math.pow(1.001,-e.deltaY);"
                "var ns=Math.max(0.05,Math.min(20,sc*factor));"
                "var ds=ns/sc;"
                "ox-=mx*(ds-1);oy-=my*(ds-1);"
                "sc=ns;applyT();"
                "},{passive:false});"
                "li.addEventListener('mousedown',function(e){"
                "if(e.button!==0)return;"
                "drag=true;sx=e.clientX-ox;sy=e.clientY-oy;"
                "li.classList.add('dragging');"
                "e.preventDefault();"
                "});"
                "document.addEventListener('mousemove',function(e){"
                "if(!drag)return;"
                "ox=e.clientX-sx;oy=e.clientY-sy;applyT();"
                "});"
                "document.addEventListener('mouseup',function(){"
                "if(drag){drag=false;li.classList.remove('dragging');}"
                "});"
                "li.addEventListener('click',function(e){"
                "e.stopPropagation();"
                "if(Date.now()<suppressClickUntil)return;"
                "if(isQuickRepeat(e.clientX,e.clientY)){"
                "ignoreNativeDbl=true;lastClick=0;"
                "toggleZoomAt(e.clientX,e.clientY);"
                "}"
                "});"
                "li.addEventListener('dblclick',function(e){"
                "e.preventDefault();"
                "e.stopPropagation();"
                "if(ignoreNativeDbl){ignoreNativeDbl=false;return;}"
                "lastClick=0;toggleZoomAt(e.clientX,e.clientY);"
                "});"
                "li.addEventListener('touchend',function(e){"
                "if(e.changedTouches.length!==1)return;"
                "var t=e.changedTouches[0];"
                "suppressClickUntil=Date.now()+450;"
                "if(isQuickRepeat(t.clientX,t.clientY)){"
                "e.preventDefault();lastClick=0;"
                "toggleZoomAt(t.clientX,t.clientY);"
                "}"
                "});"
                "})();</script>"
            )

        html.append("</body></html>")
        result = "".join(html)
        logger.log("OK: {}, skip: {}".format(cards_ok, cards_skip))
        logger.log("Img OK: {}, fail: {}".format(img_ok[0], img_fail[0]))
        return result, card_ids


_dlg = None



class EngineSetupDialog(QDialog):
    """Guided, one-click setup of what WeasyPrint needs on macOS (Homebrew: Python 3.14 + Pango).

    With Homebrew present the install runs right here with live output. Without it, a Terminal
    window opens with the official Homebrew installer followed by the two packages, because the
    Homebrew installer needs the user's password and must run interactively.
    """

    PACKAGES = ["python@3.14", "pango"]
    BREW_INSTALLER = "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setObjectName("PdfferWindow")  # same window background as the export window
        self.setWindowTitle(_t("eng_title"))
        self.setMinimumWidth(560)
        self.proc = None
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(12)
        title = QLabel(_t("eng_title"))
        f = title.font()
        f.setPointSize(f.pointSize() + 3)
        f.setBold(True)
        title.setFont(f)
        root.addWidget(title)
        intro = QLabel(_t("eng_intro"))
        intro.setWordWrap(True)
        intro.setObjectName("Secondary")
        root.addWidget(intro)

        self.rows = {}
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        for i, (key, label) in enumerate((("brew", "Homebrew"), ("python", "Python 3.14"),
                                          ("pango", "Pango"), ("engine", _t("eng_test")))):
            mark = QLabel("\u2026")
            mark.setFixedWidth(18)
            name = QLabel(label)
            detail = QLabel("")
            detail.setObjectName("Secondary")
            for col, w in enumerate((mark, name, detail)):
                w.setMinimumHeight(22)
                grid.addWidget(w, i, col)
            self.rows[key] = (mark, detail)
        grid.setColumnStretch(2, 1)
        root.addLayout(grid)

        self.note = QLabel("")
        self.note.setWordWrap(True)
        self.note.setVisible(False)
        root.addWidget(self.note)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setVisible(False)
        self.log.setMinimumHeight(160)
        self.log.setStyleSheet("font-family: Menlo, monospace; font-size: 11px;")
        root.addWidget(self.log)

        buttons = QHBoxLayout()
        self.copy_btn = QPushButton(_t("btn_eng_copy"))
        self.copy_btn.clicked.connect(self._copy)
        buttons.addWidget(self.copy_btn)
        buttons.addStretch()
        self.check_btn = QPushButton(_t("btn_engine_check"))
        self.check_btn.clicked.connect(self._refresh)
        buttons.addWidget(self.check_btn)
        self.install_btn = QPushButton(_t("btn_eng_install"))
        self.install_btn.setObjectName("Primary")
        self.install_btn.clicked.connect(self._install)
        for btn in (self.copy_btn, self.check_btn, self.install_btn):
            btn.setMinimumWidth(btn.fontMetrics().horizontalAdvance(btn.text()) + 40)
        buttons.addWidget(self.install_btn)
        close = QPushButton(_t("btn_close"))
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        root.addLayout(buttons)
        self._refresh()

    # ------------------------------------------------------------ status
    def _refresh(self):
        self.check_btn.setEnabled(False)
        self.install_btn.setEnabled(False)
        for mark, _ in self.rows.values():
            mark.setText("\u2026")
        self.owner._check_engine(force=True, then=self._show)

    def _show(self, r):
        self.report = r
        ok = {"brew": bool(r.get("brew")), "python": bool(r.get("python")),
              "pango": bool(r.get("pango")), "engine": bool(r.get("engine"))}
        details = {"brew": r.get("brew") or "", "python": r.get("python") or "",
                   "pango": "", "engine": r.get("engine") or ""}
        for key, (mark, detail) in self.rows.items():
            mark.setText("\u2713" if ok[key] else "\u2715")
            mark.setStyleSheet("color: {}; font-weight: 700;".format("#28a745" if ok[key] else "#ff3b30"))
            detail.setText(details[key])
        self.check_btn.setEnabled(True)
        if not r.get("macos", True):
            self._say(_t("eng_unsupported"))
            self.install_btn.setEnabled(False)
        elif ok["engine"]:
            self._say(_t("eng_done"))
            self.install_btn.setEnabled(False)
        else:
            self.install_btn.setEnabled(self.proc is None)

    def _say(self, text):
        self.note.setText(text)
        self.note.setVisible(bool(text))

    def commands(self):
        brew_line = '/bin/bash -c "$(curl -fsSL {})"'.format(self.BREW_INSTALLER)
        return [brew_line, "brew install " + " ".join(self.PACKAGES)]

    def _copy(self):
        QApplication.clipboard().setText("\n".join(self.commands()))

    # ------------------------------------------------------------ install
    def _install(self):
        brew = (getattr(self, "report", None) or {}).get("brew")
        if brew:
            self._install_with_brew(brew)
        else:
            self._install_in_terminal()

    def _install_with_brew(self, brew):
        self.install_btn.setEnabled(False)
        self.log.clear()
        self.log.setVisible(True)
        self._say(_t("eng_running"))
        self.proc = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PATH", os.path.dirname(brew) + ":" + env.value("PATH", "/usr/bin:/bin"))
        env.insert("HOMEBREW_NO_INSTALL_CLEANUP", "1")
        self.proc.setProcessEnvironment(env)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._pump)
        self.proc.finished.connect(self._installed)
        self.proc.start(brew, ["install"] + self.PACKAGES)

    def _pump(self):
        text = bytes(self.proc.readAllStandardOutput()).decode("utf-8", "replace")
        self.log.appendPlainText(text.rstrip())
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def _installed(self, code, _status):
        self.proc = None
        if code != 0:
            self._say(_t("eng_failed"))
        self._refresh()

    def _install_in_terminal(self):
        script = "\n".join([
            "#!/bin/bash",
            "echo 'AnkiPdffer: installing the PDF engine (Homebrew, Python 3.14, Pango)'",
            "if ! command -v brew >/dev/null 2>&1; then",
            "  " + self.commands()[0],
            "  eval \"$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)\"",
            "fi",
            self.commands()[1] + " && echo && echo 'Done - return to Anki and click Check again.'",
            "",
        ])
        path = os.path.join(tempfile.gettempdir(), "AnkiPdffer-install-pdf-engine.command")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(script)
        os.chmod(path, 0o755)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        self._say(_t("eng_terminal"))

    def reject(self):
        if self.proc is not None:  # keep the install running only while the guide is open
            self.proc.kill()
        super().reject()

    def accept(self):
        if self.proc is not None:
            self.proc.kill()
        super().accept()


def _dialog_alive(dlg):
    try:
        dlg.windowTitle()  # raises RuntimeError once the C++ object is gone
        return True
    except (RuntimeError, AttributeError):
        return False


def _get_dialog():
    """Return THE export window, creating it only when needed.

    One window is reused for the whole session (so it can be restored instead of
    stacking new ones); it is rebuilt only when the collection/profile changed.
    """
    global _dlg
    if mw is None or mw.col is None:
        return None
    if _dlg is not None and (not _dialog_alive(_dlg) or _dlg._col_ref is not mw.col):
        if _dialog_alive(_dlg):
            _dlg.deleteLater()
        _dlg = None
    if _dlg is None:
        _dlg = PDFExportDialog(mw)
    elif not _dlg.isVisible():
        _dlg.refresh_collection()
    return _dlg


def show_export_dialog():
    dlg = _get_dialog()
    if dlg is None:
        showWarning(_t("msg_no_collection"))
        return
    # restore from minimized / behind other windows rather than opening another one
    dlg.setWindowState(
        (dlg.windowState() & ~Qt.WindowState.WindowMinimized) | Qt.WindowState.WindowActive)
    dlg.show()
    dlg.raise_()
    dlg.activateWindow()


def _quick_legacy_export():
    """Open the currently focused deck as Legacy HTML (Shift+Alt+P shortcut)."""
    dlg = _get_dialog()
    if dlg is None:
        return
    cur = mw.col.decks.current()
    if cur:
        dlg.select_deck(cur["name"])
    dlg._on_legacy()


def _rebuild_dialog():
    """Recreate the window after a language change (strings are read at build time)."""
    global _dlg
    selected, was_visible = None, False
    if _dlg is not None and _dialog_alive(_dlg):
        selected, was_visible = _dlg._sel(), _dlg.isVisible()
        _dlg.hide()
        _dlg.deleteLater()
    _dlg = None
    _retranslate_menu()
    if was_visible and mw is not None and mw.col is not None:
        dlg = _get_dialog()
        if selected:
            dlg.select_deck(selected)
        dlg.tabs.setCurrentIndex(dlg.stack.count() - 1)  # back on Settings, where the language was changed
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()


_dev_menu = QMenu(_t("menu_root"), mw)
mw.form.menuTools.addMenu(_dev_menu)

action = QAction(_t("menu_action"), mw)
action.triggered.connect(show_export_dialog)
_dev_menu.addAction(action)

_quick_legacy_action = QAction(_t("menu_quick_legacy"), mw)
_quick_legacy_action.setShortcut(QKeySequence("Shift+Alt+P"))
_quick_legacy_action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
_quick_legacy_action.triggered.connect(_quick_legacy_export)
_dev_menu.addAction(_quick_legacy_action)


def _retranslate_menu():
    _dev_menu.setTitle(_t("menu_root"))
    action.setText(_t("menu_action"))
    _quick_legacy_action.setText(_t("menu_quick_legacy"))
