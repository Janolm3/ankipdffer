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


class InlineRadioGroup(QWidget):
    def __init__(self, options, default=0, parent=None):
        super().__init__(parent)
        ly = QHBoxLayout()
        ly.setContentsMargins(0, 0, 0, 0)
        ly.setSpacing(12)
        self.group = QButtonGroup(self)
        self.buttons = []
        self._current_index = default if 0 <= default < len(options) else 0
        for i, label in enumerate(options):
            rb = QRadioButton(label)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            if i == default:
                rb.setChecked(True)
            rb.toggled.connect(lambda checked, idx=i: self._on_toggled(idx, checked))
            self.group.addButton(rb, i)
            self.buttons.append(rb)
            ly.addWidget(rb)
        ly.addStretch()
        self.setLayout(ly)

    def _on_toggled(self, idx, checked):
        if checked:
            self._current_index = idx

    def currentIndex(self):
        return self._current_index

    def setCurrentIndex(self, idx):
        if 0 <= idx < len(self.buttons):
            self._current_index = idx
            self.buttons[idx].setChecked(True)


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
EXPORT_BUILD = "1.4.0-20261101"
TOOL_NAME = "AnkiPdffer"
TOOL_URL = "https://ankiweb.net/shared/info/1987190048"
TOOL_URL_DISPLAY = "ankiweb.net/shared/info/1987190048"


def _addon_version(default="1.4.0"):
    try:
        manifest_path = os.path.join(os.path.dirname(__file__), "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        return manifest.get("human_version", default)
    except Exception:
        return default


class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)

    def javaScriptConsoleMessage(self, level, msg, line, src):
        logger.log("JS [{}] L{}: {}".format(level, line, msg))


class FieldConfigWidget(QWidget):
    """One row of the Fields tab. `changed` fires on any edit so settings autosave."""

    changed = pyqtSignal()

    def __init__(self, field_name, is_front=False, nt_id=0, nt_name="", config=None, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.nt_id = nt_id
        self.nt_name = nt_name
        root = QVBoxLayout()
        root.setContentsMargins(8, 4, 8, 4)
        root.setSpacing(0)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.export_cb = QCheckBox()
        self.export_cb.setChecked(True)
        row.addWidget(self.export_cb)
        self.name_label = QLabel(field_name)
        self.name_label.setTextFormat(Qt.TextFormat.PlainText)
        name_font = self.name_label.font()
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        self.name_label.setMinimumWidth(120)
        self.name_label.setToolTip(field_name)
        row.addWidget(self.name_label)
        self.section_combo = NoScrollComboBox()
        self.section_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.section_combo.addItems([_t("sec_front"), _t("sec_back"), _t("sec_extra")])
        self.section_combo.setCurrentIndex(0 if is_front else 1)
        self.section_combo.setMinimumWidth(160)
        row.addWidget(self.section_combo)
        self.size_radio = InlineRadioGroup(["S", "M", "L", "XL"], default=(2 if is_front else 1))
        row.addWidget(self.size_radio)
        self.bold_cb = QCheckBox("B")
        self.bold_cb.setChecked(is_front)
        f_bold = self.bold_cb.font()
        f_bold.setBold(True)
        self.bold_cb.setFont(f_bold)
        row.addWidget(self.bold_cb)
        self.label_cb = QCheckBox(_t("field_lbl_label"))
        self.label_cb.setChecked(not is_front)
        row.addWidget(self.label_cb)
        row.addStretch()
        self.adv_btn = QPushButton("\u22ef")
        self.adv_btn.setObjectName("FieldMoreBtn")
        self.adv_btn.setFixedSize(28, 26)
        self.adv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.adv_btn.clicked.connect(self._toggle)
        row.addWidget(self.adv_btn)
        root.addLayout(row)

        self.adv_panel = QWidget()
        self.adv_panel.setVisible(False)
        ap = QHBoxLayout()
        ap.setContentsMargins(32, 4, 0, 6)
        ap.setSpacing(10)
        ap.addWidget(QLabel(_t("field_lbl_bg")))
        self.bg_combo = NoScrollComboBox()
        self.bg_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.bg_combo.addItems(_t("field_bg"))
        ap.addWidget(self.bg_combo)
        ap.addWidget(QLabel(_t("field_lbl_color")))
        self.color_combo = NoScrollComboBox()
        self.color_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.color_combo.addItems(_t("field_color"))
        ap.addWidget(self.color_combo)
        ap.addWidget(QLabel(_t("field_lbl_align")))
        self.align_combo = NoScrollComboBox()
        self.align_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.align_combo.addItems(_t("field_align"))
        ap.addWidget(self.align_combo)
        self.italic_cb = QCheckBox("I")
        f_ital = self.italic_cb.font()
        f_ital.setItalic(True)
        self.italic_cb.setFont(f_ital)
        ap.addWidget(self.italic_cb)
        self.underline_cb = QCheckBox("U")
        f_under = self.underline_cb.font()
        f_under.setUnderline(True)
        self.underline_cb.setFont(f_under)
        ap.addWidget(self.underline_cb)
        ap.addStretch()
        self.adv_panel.setLayout(ap)
        root.addWidget(self.adv_panel)
        self.setLayout(root)

        if config:
            self.set_config(config)
        self._wire_changes()

    def _wire_changes(self):
        emit = lambda *_: self.changed.emit()
        for cb in (self.export_cb, self.bold_cb, self.label_cb, self.italic_cb, self.underline_cb):
            cb.toggled.connect(emit)
        for combo in (self.section_combo, self.bg_combo, self.color_combo, self.align_combo):
            combo.currentIndexChanged.connect(emit)
        self.size_radio.group.idToggled.connect(emit)

    def _toggle(self):
        v = not self.adv_panel.isVisible()
        self.adv_panel.setVisible(v)
        self.adv_btn.setText("\u2715" if v else "\u22ef")

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

        is_dark = _is_dark_mode()
        if is_dark:
            bg_color = "#101010"
            card_bg = "#18181b"
            panel_bg = "#202022"
            border_color = "#27272a"
            text_color = "#f4f4f5"
            muted_text = "#a1a1aa"
            accent_color = "#3b82f6"
            accent_hover = "#60a5fa"
            hover_bg = "#27272a"
            selected_bg = "rgba(59, 130, 246, 0.15)"
        else:
            bg_color = "#fcfcfc"
            card_bg = "#f4f4f5"
            panel_bg = "#ffffff"
            border_color = "#e4e4e7"
            text_color = "#18181b"
            muted_text = "#71717a"
            accent_color = "#2563eb"
            accent_hover = "#3b82f6"
            hover_bg = "#e4e4e7"
            selected_bg = "rgba(37, 99, 235, 0.12)"

        dialog_css = """
            PDFExportDialog, QStackedWidget, QStackedWidget > QWidget {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollArea > QWidget {{
                background-color: transparent;
            }}
            QWidget#FieldsContainer {{
                background-color: transparent;
            }}
            FieldConfigWidget {{
                background-color: {card_bg};
                border-bottom: 1px solid {border_color};
                border-radius: 4px;
                padding: 6px;
            }}
            QLabel, QCheckBox, QRadioButton, QGroupBox {{
                background-color: transparent;
                color: {text_color};
            }}
            QLabel {{
                font-size: 13px;
            }}
            QLabel#HintLabel {{
                color: {muted_text};
                font-size: 11px;
                padding: 0 4px 4px;
            }}
            QLabel#VersionLabel {{
                color: {muted_text};
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel#SettingsInfoLabel {{
                color: {muted_text};
                font-size: 12px;
            }}
            QLabel#BusyLabel {{
                color: {muted_text};
                font-size: 12px;
                font-weight: 600;
            }}
            QGroupBox {{
                font-size: 13px;
                font-weight: 700;
                color: {text_color};
                border: none;
                border-top: 1px solid {border_color};
                margin-top: 18px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 0px;
                padding: 0 8px 0 0;
                color: {accent_color};
            }}
            QComboBox, QSpinBox, QDoubleSpinBox, NoScrollComboBox, QLineEdit, QPlainTextEdit {{
                background-color: {panel_bg};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px 10px;
                color: {text_color};
                font-size: 13px;
                min-height: 20px;
            }}
            QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover {{
                border-color: {accent_color};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {muted_text};
                width: 0;
                height: 0;
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                selection-background-color: {accent_color};
                selection-color: #ffffff;
                color: {text_color};
                outline: none;
                border-radius: 6px;
            }}
            QCheckBox {{
                spacing: 8px;
                font-size: 13px;
                color: {text_color};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {border_color};
                border-radius: 4px;
                background: {panel_bg};
            }}
            QCheckBox::indicator:hover {{
                border-color: {accent_color};
            }}
            QCheckBox::indicator:checked {{
                border-color: {accent_color};
                background-color: {accent_color};
                background-image: qradialgradient(cx:0.5, cy:0.5, radius:0.25, fx:0.5, fy:0.5, stop:0 #ffffff, stop:0.7 #ffffff, stop:0.8 {accent_color}, stop:1.0 {accent_color});
            }}
            QRadioButton {{
                spacing: 6px;
                padding: 4px 0;
                margin: 0;
                border: none;
                background: transparent;
                font-size: 13px;
                color: {text_color};
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {border_color};
                border-radius: 9px;
                background: {panel_bg};
            }}
            QRadioButton::indicator:hover {{
                border-color: {accent_color};
            }}
            QRadioButton::indicator:checked {{
                border-color: {accent_color};
                background-color: {panel_bg};
                background-image: qradialgradient(cx:0.5, cy:0.5, radius:0.35, fx:0.5, fy:0.5, stop:0 {accent_color}, stop:0.7 {accent_color}, stop:0.8 {panel_bg}, stop:1.0 {panel_bg});
            }}
            QPushButton#SmallBtn, QPushButton#DangerBtn, QPushButton#FieldMoreBtn {{
                background-color: {panel_bg};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 5px 12px;
                color: {text_color};
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton#FieldMoreBtn {{
                padding: 0;
                font-size: 14px;
            }}
            QPushButton#DangerBtn {{
                color: #ef4444;
            }}
            QPushButton#SmallBtn:hover, QPushButton#FieldMoreBtn:hover {{
                border-color: {accent_color};
            }}
            QPushButton#DangerBtn:hover {{
                border-color: #ef4444;
            }}
            QPushButton#SmallBtn:disabled {{
                color: {muted_text};
            }}
            QLabel#NtHeader {{
                color: {accent_color};
                font-size: 12px;
                font-weight: 700;
                padding: 12px 4px 2px;
            }}
            QLabel#CountLabel {{
                color: {muted_text};
                font-size: 12px;
            }}
            QLabel#CountLabel[error="true"] {{
                color: #ef4444;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {border_color};
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {accent_color};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: none;
                border: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """.format(
            bg_color=bg_color,
            card_bg=card_bg,
            panel_bg=panel_bg,
            border_color=border_color,
            text_color=text_color,
            muted_text=muted_text,
            accent_color=accent_color
        )
        self.setStyleSheet(dialog_css)

        self._busy_timer = QTimer(self)
        self._busy_timer.timeout.connect(self._animate_busy)
        self._busy_val = 0
        self._spinner_idx = 0
        self._spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._base_busy_message = ""

        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            w = max(980, min(int(sg.width() * 0.78), 1280))
            h = max(640, min(int(sg.height() * 0.78), 820))
            self.resize(w, h)
            self.setMinimumSize(860, 560)
        else:
            self.resize(1100, 720)
            self.setMinimumSize(860, 560)
        self._active_export_theme_index = None
        self._busy_depth = 0
        self._font_debug_logged_modes = set()
        self._pdf_ready_logged = False

        root = QVBoxLayout()
        root.setContentsMargins(18, 18, 18, 14)
        root.setSpacing(10)

        deck_group = QGroupBox(_t("deck_group"))
        dg = QHBoxLayout()
        dg.addWidget(QLabel(_t("deck_lbl")))
        self.deck_combo = QComboBox()
        self.deck_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        dg.addWidget(self.deck_combo)
        dg.addSpacing(12)
        dg.addWidget(QLabel(_t("subdeck_lbl")))
        self.subdeck_combo = QComboBox()
        self.subdeck_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        dg.addWidget(self.subdeck_combo)
        dg_outer = QVBoxLayout()
        dg_outer.setSpacing(8)
        dg_outer.addLayout(dg)
        fr = QHBoxLayout()
        fr.addWidget(QLabel(_t("lbl_filter")))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(_t("ph_filter"))
        self.filter_edit.setToolTip(_t("tip_filter"))
        self.filter_edit.setClearButtonEnabled(True)
        fr.addWidget(self.filter_edit, 1)
        self.count_label = QLabel("")
        self.count_label.setObjectName("CountLabel")
        self.count_label.setMinimumWidth(190)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        fr.addWidget(self.count_label)
        dg_outer.addLayout(fr)
        deck_group.setLayout(dg_outer)
        root.addWidget(deck_group)
        self._count_timer = QTimer(self)
        self._count_timer.setSingleShot(True)
        self._count_timer.timeout.connect(self._update_count)
        self.filter_edit.textChanged.connect(lambda *_: self._count_timer.start(350))

        content_frame = QFrame()
        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(176)
        self.sidebar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sidebar.setStyleSheet("""
            QListWidget#Sidebar {{
                background: transparent;
                border: none;
                border-right: 1px solid {border_color};
                outline: none;
                padding-top: 8px;
            }}
            QListWidget#Sidebar::item {{
                padding: 10px 14px;
                margin: 2px 10px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                color: {muted_text};
                border-left: 3px solid transparent;
            }}
            QListWidget#Sidebar::item:selected {{
                background: {selected_bg};
                color: {accent_color};
                border-left: 3px solid {accent_color};
                border-radius: 0px 6px 6px 0px;
                padding-left: 11px;
            }}
            QListWidget#Sidebar::item:hover:!selected {{
                background: {hover_bg};
                color: {text_color};
            }}
        """.format(
            border_color=border_color,
            muted_text=muted_text,
            accent_color=accent_color,
            hover_bg=hover_bg,
            selected_bg=selected_bg,
            text_color=text_color
        ))
        content_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack, 1)

        # --- Tab: Basic ---
        basic = QWidget()
        bl = QFormLayout(basic)
        bl.setContentsMargins(28, 22, 28, 22)
        bl.setHorizontalSpacing(18)
        bl.setVerticalSpacing(18)
        bl.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.theme_radio = InlineRadioGroup(
            [_t("theme_light"), _t("theme_dark"), _t("theme_pro")], default=0)
        bl.addRow(_t("lbl_theme"), self.theme_radio)

        f_row = QHBoxLayout()
        self.font_combo = NoScrollComboBox()
        self.font_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for name, _ in FONT_OPTIONS:
            self.font_combo.addItem(name)
        self.font_combo.setCurrentIndex(0)
        self.font_combo.setMinimumWidth(150)
        f_row.addWidget(self.font_combo)
        f_row.addSpacing(12)
        f_row.addWidget(QLabel(_t("lbl_size")))
        self.fontsize_spin = QSpinBox()
        self.fontsize_spin.setRange(10, 24)
        self.fontsize_spin.setValue(13)
        self.fontsize_spin.setSuffix(" px")
        f_row.addWidget(self.fontsize_spin)
        f_row.addStretch()
        bl.addRow(_t("lbl_font"), f_row)

        w_row = QHBoxLayout()
        self.width_radio = InlineRadioGroup([
            _t("width_narrow"), _t("width_medium"), _t("width_wide"),
            _t("width_full"), _t("width_custom"),
        ], default=1)
        w_row.addWidget(self.width_radio)
        self.width_spin = NoScrollSpinBox()
        self.width_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.width_spin.setRange(300, 3000)
        self.width_spin.setValue(800)
        self.width_spin.setSuffix(" px")
        self.width_spin.setVisible(False)
        w_row.addWidget(self.width_spin)
        self.width_radio.group.idToggled.connect(self._on_width_radio_changed)
        w_row.addStretch()
        bl.addRow(_t("lbl_width"), w_row)

        l_row = QHBoxLayout()
        self.layout_radio = InlineRadioGroup(
            [_t("layout_standard"), _t("layout_compact")], default=1)
        l_row.addWidget(self.layout_radio)
        l_row.addSpacing(44)
        l_row.addWidget(QLabel(_t("lbl_source")))

        self.render_radio = InlineRadioGroup(
            [_t("source_fields"), _t("source_cards")], default=0)
        self.render_radio.group.idToggled.connect(self._on_render_radio_changed)
        l_row.addWidget(self.render_radio)
        l_row.addStretch()
        bl.addRow(_t("lbl_layout"), l_row)

        r_cb1 = QHBoxLayout()
        r_cb1.setSpacing(16)
        self.show_title_cb = QCheckBox(_t("cb_title"))
        self.show_title_cb.setChecked(True)
        r_cb1.addWidget(self.show_title_cb)
        self.card_numbers_cb = QCheckBox(_t("cb_numbers"))
        r_cb1.addWidget(self.card_numbers_cb)
        r_cb1.addStretch()
        bl.addRow(QLabel(""), r_cb1)

        r_cb2 = QHBoxLayout()
        r_cb2.setSpacing(16)
        self.zebra_cb = QCheckBox(_t("cb_zebra"))
        r_cb2.addWidget(self.zebra_cb)
        self.high_contrast_cb = QCheckBox(_t("cb_high_contrast"))
        r_cb2.addWidget(self.high_contrast_cb)
        r_cb2.addStretch()
        bl.addRow(QLabel(""), r_cb2)

        self.qa_combo = NoScrollComboBox()
        self.qa_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.qa_combo.addItems([_t("qa_together"), _t("qa_key"), _t("qa_pages")])
        self.qa_combo.setToolTip(_t("tip_qa"))
        self.qa_combo.setMinimumWidth(260)
        qa_row = QHBoxLayout()
        qa_row.addWidget(self.qa_combo)
        qa_row.addStretch()
        qa_lbl = QLabel(_t("lbl_qa"))
        qa_lbl.setToolTip(_t("tip_qa"))
        bl.addRow(qa_lbl, qa_row)

        self.cloze_combo = NoScrollComboBox()
        self.cloze_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.cloze_combo.addItems([_t("cloze_reveal"), _t("cloze_hide"),
                                   _t("cloze_both"), _t("cloze_native")])
        self.cloze_combo.setToolTip(_t("tip_cloze"))
        self.cloze_combo.setMinimumWidth(260)
        cz_row = QHBoxLayout()
        cz_row.addWidget(self.cloze_combo)
        cz_row.addStretch()
        cz_lbl = QLabel(_t("lbl_cloze"))
        cz_lbl.setToolTip(_t("tip_cloze"))
        bl.addRow(cz_lbl, cz_row)

        self.io_combo = NoScrollComboBox()
        self.io_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.io_combo.addItems([_t("io_all"), _t("io_each")])
        self.io_combo.setToolTip(_t("tip_io"))
        self.io_combo.setMinimumWidth(260)
        io_row = QHBoxLayout()
        io_row.addWidget(self.io_combo)
        io_row.addStretch()
        io_lbl = QLabel(_t("lbl_io"))
        io_lbl.setToolTip(_t("tip_io"))
        bl.addRow(io_lbl, io_row)
        self.stack.addWidget(basic)
        self.sidebar.addItem(_t("tab_basic"))

        # --- Tab: Advanced ---
        adv = QWidget()
        avl = QFormLayout(adv)
        avl.setContentsMargins(28, 22, 28, 22)
        avl.setHorizontalSpacing(18)
        avl.setVerticalSpacing(16)

        def _spin(lo, hi, val, sfx):
            sp = NoScrollSpinBox()
            sp.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            sp.setRange(lo, hi)
            sp.setValue(val)
            sp.setSuffix(sfx)
            sp.setMaximumWidth(100)
            return sp

        self.page_combo = QComboBox()
        self.page_combo.addItems(["A4", "Letter", "A3", "A5"])
        self.page_combo.setMaximumWidth(100)
        avl.addRow(_t("lbl_page"), self.page_combo)

        self.margin_spin = _spin(5, 40, 15, " mm")
        avl.addRow(_t("lbl_margins"), self.margin_spin)

        self.top_margin_spin = _spin(0, 40, 15, " mm")
        avl.addRow(_t("lbl_top_margin"), self.top_margin_spin)

        self.padding_spin = _spin(2, 50, 12, " px")
        avl.addRow(_t("lbl_padding"), self.padding_spin)

        self.gap_spin = _spin(0, 80, 8, " px")
        avl.addRow(_t("lbl_gap"), self.gap_spin)

        self.lh_spin = NoScrollDoubleSpinBox()
        self.lh_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.lh_spin.setRange(1.0, 2.5)
        self.lh_spin.setValue(1.40)
        self.lh_spin.setSingleStep(0.05)
        self.lh_spin.setMaximumWidth(100)
        avl.addRow(_t("lbl_lineheight"), self.lh_spin)

        self.img_h_spin = _spin(60, 800, 240, " px")
        avl.addRow(_t("lbl_maximg"), self.img_h_spin)

        ra = QHBoxLayout()
        self.card_style_combo = QComboBox()
        self.card_style_combo.addItems([
            _t("style_rounded"), _t("style_sharp"), _t("style_separator"),
            _t("style_double"), _t("style_none"),
        ])
        ra.addWidget(self.card_style_combo)
        ra.addSpacing(16)
        self.strip_html_cb = QCheckBox(_t("cb_strip_html"))
        ra.addWidget(self.strip_html_cb)
        ra.addStretch()
        avl.addRow(_t("lbl_card_style"), ra)

        self.order_combo = QComboBox()
        self.order_combo.addItems([_t("order_deck"), _t("order_created"), _t("order_shuffle")])
        self.order_combo.setMaximumWidth(220)
        avl.addRow(_t("lbl_order"), self.order_combo)

        self.page_numbers_cb = QCheckBox(_t("cb_page_numbers"))
        avl.addRow(QLabel(""), self.page_numbers_cb)
        self.stack.addWidget(adv)
        self.sidebar.addItem(_t("tab_advanced"))

        # --- Tab: Fields ---
        self.fields_tab = QWidget()
        fl = QVBoxLayout(self.fields_tab)
        fl.setContentsMargins(24, 24, 24, 24)
        fl.setSpacing(20)
        hint = QLabel(_t("fields_hint"))
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)
        fl.addWidget(hint)
        self.fields_scroll = QScrollArea()
        self.fields_scroll.setWidgetResizable(True)
        self.fields_container = QWidget()
        self.fields_container.setObjectName("FieldsContainer")
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setContentsMargins(2, 2, 2, 2)
        self.fields_layout.setSpacing(1)
        self.fields_layout.addStretch()
        self.fields_scroll.setWidget(self.fields_container)
        fl.addWidget(self.fields_scroll)
        self.stack.addWidget(self.fields_tab)
        self.sidebar.addItem(_t("tab_fields"))

        # --- Tab: Settings ---
        settings_tab = QWidget()
        stl = QVBoxLayout(settings_tab)
        stl.setSpacing(16)
        stl.setContentsMargins(24, 24, 24, 24)

        auto_lbl = QLabel(_t("settings_autosave"))
        auto_lbl.setObjectName("HintLabel")
        auto_lbl.setWordWrap(True)
        stl.addWidget(auto_lbl)

        presets_group = QGroupBox(_t("grp_presets"))
        pg = QVBoxLayout()
        pg.setSpacing(10)
        pr = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(220)
        pr.addWidget(self.preset_combo, 1)
        self.preset_apply_btn = QPushButton(_t("btn_preset_apply"))
        self.preset_apply_btn.setObjectName("SmallBtn")
        self.preset_apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preset_apply_btn.clicked.connect(self._apply_preset)
        pr.addWidget(self.preset_apply_btn)
        self.preset_delete_btn = QPushButton(_t("btn_preset_delete"))
        self.preset_delete_btn.setObjectName("DangerBtn")
        self.preset_delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preset_delete_btn.clicked.connect(self._delete_preset)
        pr.addWidget(self.preset_delete_btn)
        pg.addLayout(pr)
        pr2 = QHBoxLayout()
        self.preset_save_btn = QPushButton(_t("btn_preset_save"))
        self.preset_save_btn.setObjectName("SmallBtn")
        self.preset_save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preset_save_btn.clicked.connect(self._save_preset)
        pr2.addWidget(self.preset_save_btn)
        self.reset_btn = QPushButton(_t("btn_reset_all"))
        self.reset_btn.setObjectName("DangerBtn")
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.clicked.connect(self._reset_settings)
        pr2.addWidget(self.reset_btn)
        pr2.addStretch()
        pg.addLayout(pr2)
        presets_group.setLayout(pg)
        stl.addWidget(presets_group)

        self.settings_info = QLabel("")
        self.settings_info.setObjectName("SettingsInfoLabel")
        self.settings_info.setWordWrap(True)
        self.settings_info.setVisible(False)
        stl.addWidget(self.settings_info)

        lang_ly = QHBoxLayout()
        lang_ly.addWidget(QLabel(_t("grp_language") + ":"))
        self.lang_combo = NoScrollComboBox()
        self.lang_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for code, native in LANGUAGES.items():
            self.lang_combo.addItem(native, code)
        self.lang_combo.setCurrentIndex(max(0, self.lang_combo.findData(_lang)))
        self.lang_combo.setMinimumWidth(180)
        lang_ly.addWidget(self.lang_combo)
        lang_ly.addStretch()
        stl.addLayout(lang_ly)

        dbg_ly = QHBoxLayout()
        self.debug_cb = QCheckBox(_t("cb_debug"))
        dbg_ly.addWidget(self.debug_cb)
        self.log_btn = QPushButton(_t("btn_logs"))
        self.log_btn.setObjectName("SmallBtn")
        self.log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.log_btn.setVisible(False)
        self.log_btn.clicked.connect(self._show_logs)
        dbg_ly.addWidget(self.log_btn)
        dbg_ly.addStretch()
        stl.addLayout(dbg_ly)
        self.debug_cb.toggled.connect(self.log_btn.setVisible)

        stl.addStretch()
        self.stack.addWidget(settings_tab)
        self.sidebar.addItem(_t("tab_settings"))

        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

        root.addWidget(content_frame)

        # --- Bottom buttons ---
        bottom = QHBoxLayout()
        bottom.setContentsMargins(12, 4, 12, 0)
        addon_version = _addon_version()
        v_lbl = QLabel(f"v {addon_version}")
        v_lbl.setObjectName("VersionLabel")
        bottom.addWidget(v_lbl)
        bottom.addStretch()

        self.busy_wrap = QWidget()
        busy_ly = QHBoxLayout(self.busy_wrap)
        busy_ly.setContentsMargins(0, 0, 10, 0)
        busy_ly.setSpacing(8)
        self.busy_bar = QProgressBar()
        self.busy_bar.setObjectName("BusyBar")
        busy_bar_bg = "#0f172a" if is_dark else "#f1f5f9"
        busy_bar_border = "1px solid #334155" if is_dark else "1px solid #cbd5e1"
        busy_bar_chunk = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #60a5fa)" if is_dark else "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #3b82f6)"
        self.busy_bar.setStyleSheet("""
            QProgressBar#BusyBar {{
                background: {busy_bar_bg};
                border: {busy_bar_border};
                border-radius: 4px;
            }}
            QProgressBar#BusyBar::chunk {{
                background: {busy_bar_chunk};
                border-radius: 3px;
            }}
        """.format(busy_bar_bg=busy_bar_bg, busy_bar_border=busy_bar_border, busy_bar_chunk=busy_bar_chunk))
        self.busy_bar.setRange(0, 100)
        self.busy_bar.setValue(0)
        self.busy_bar.setFixedSize(92, 10)
        self.busy_bar.setTextVisible(False)
        busy_ly.addWidget(self.busy_bar)
        self.busy_label = QLabel("")
        self.busy_label.setObjectName("BusyLabel")
        self.busy_label.setMinimumWidth(180)
        busy_ly.addWidget(self.busy_label)
        self.busy_wrap.setVisible(False)
        bottom.addWidget(self.busy_wrap)

        self.grid_cb = QCheckBox(_t("cb_grid"))
        bottom.addWidget(self.grid_cb)
        bottom.addSpacing(6)

        _btn_base = (
            "QPushButton{{"
            "border:1px solid {brd};background:{bg};color:{fg};"
            "border-radius:6px;padding:7px 18px;font-size:13px;"
            "font-weight:600;letter-spacing:0.01em}}"
            "QPushButton:hover{{background:{hover};border-color:{hover_brd}}}"
            "QPushButton:pressed{{background:{pressed};border-color:{pressed_brd}}}"
            "QPushButton:disabled{{opacity:0.5}}"
        )

        if is_dark:
            legacy_style = _btn_base.format(
                brd="#27272a", bg="transparent", fg="#e4e4e7",
                hover="#202022", hover_brd="#27272a",
                pressed="#18181b", pressed_brd="#27272a"
            )
            preview_style = _btn_base.format(
                brd="#27272a", bg="transparent", fg="#e4e4e7",
                hover="#202022", hover_brd="#27272a",
                pressed="#18181b", pressed_brd="#27272a"
            )
            export_style = _btn_base.format(
                brd="transparent", bg="qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #3b82f6)", fg="#ffffff",
                hover="qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #60a5fa)", hover_brd="transparent",
                pressed="qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #2563eb)", pressed_brd="transparent"
            )
        else:
            legacy_style = _btn_base.format(
                brd="#e4e4e7", bg="transparent", fg="#18181b",
                hover="#f4f4f5", hover_brd="#e4e4e7",
                pressed="#e4e4e7", pressed_brd="#e4e4e7"
            )
            preview_style = _btn_base.format(
                brd="#e4e4e7", bg="transparent", fg="#18181b",
                hover="#f4f4f5", hover_brd="#e4e4e7",
                pressed="#e4e4e7", pressed_brd="#e4e4e7"
            )
            export_style = _btn_base.format(
                brd="transparent", bg="qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #3b82f6)", fg="#ffffff",
                hover="qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #60a5fa)", hover_brd="transparent",
                pressed="qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #2563eb)", pressed_brd="transparent"
            )

        self.legacy_btn = QPushButton(_t("btn_legacy"))
        self.legacy_btn.setMinimumHeight(34)
        self.legacy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.legacy_btn.setStyleSheet(legacy_style)
        self.legacy_btn.clicked.connect(self._on_legacy)
        bottom.addWidget(self.legacy_btn)

        self.preview_btn = QPushButton(_t("btn_preview"))
        self.preview_btn.setMinimumHeight(34)
        self.preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_btn.setStyleSheet(preview_style)
        self.preview_btn.clicked.connect(self._on_preview)
        bottom.addWidget(self.preview_btn)

        self.export_btn = QPushButton(_t("btn_export"))
        self.export_btn.setMinimumHeight(34)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setStyleSheet(export_style)
        self.export_btn.clicked.connect(self._on_export)
        bottom.addWidget(self.export_btn)
        root.addLayout(bottom)
        self.setLayout(root)
        self._create_busy_overlay()

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

    def _create_busy_overlay(self):
        is_dark = _is_dark_mode()
        self.busy_overlay = QFrame(self)
        self.busy_overlay.setObjectName("BusyOverlay")
        self.busy_overlay.setCursor(Qt.CursorShape.WaitCursor)
        overlay_bg = "rgba(16, 16, 16, 210)" if is_dark else "rgba(255, 255, 255, 210)"
        panel_bg_overlay = "#18181b" if is_dark else "#ffffff"
        border_overlay = "rgba(59, 130, 246, 0.4)" if is_dark else "rgba(37, 99, 235, 0.3)"
        label_overlay = "#f4f4f5" if is_dark else "#18181b"
        hint_overlay = "#a1a1aa" if is_dark else "#71717a"
        bar_bg = "#101010" if is_dark else "#f4f4f5"
        bar_border = "1px solid #27272a" if is_dark else "1px solid #e4e4e7"
        bar_chunk = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #3b82f6)" if is_dark else "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #3b82f6)"
        self.busy_overlay.setStyleSheet("""
            QFrame#BusyOverlay {{
                background: {overlay_bg};
                border: none;
            }}
            QFrame#BusyPanel {{
                background: {panel_bg_overlay};
                border: 1px solid {border_overlay};
                border-radius: 12px;
                min-width: 300px;
            }}
            QLabel#BusyOverlayLabel {{
                color: {label_overlay};
                font-size: 15px;
                font-weight: 600;
                font-family: system-ui, -apple-system, sans-serif;
            }}
            QLabel#BusyOverlayHint {{
                color: {hint_overlay};
                font-size: 11px;
                font-weight: 500;
                font-family: system-ui, -apple-system, sans-serif;
            }}
            QProgressBar#BusyOverlayBar {{
                background: {bar_bg};
                border: {bar_border};
                border-radius: 5px;
            }}
            QProgressBar#BusyOverlayBar::chunk {{
                background: {bar_chunk};
                border-radius: 4px;
            }}
        """.format(
            overlay_bg=overlay_bg,
            panel_bg_overlay=panel_bg_overlay,
            border_overlay=border_overlay,
            label_overlay=label_overlay,
            hint_overlay=hint_overlay,
            bar_bg=bar_bg,
            bar_border=bar_border,
            bar_chunk=bar_chunk
        ))
        overlay_ly = QVBoxLayout(self.busy_overlay)
        overlay_ly.setContentsMargins(0, 0, 0, 0)
        overlay_ly.addStretch()

        self.busy_panel = QFrame(self.busy_overlay)
        self.busy_panel.setObjectName("BusyPanel")
        panel_ly = QVBoxLayout(self.busy_panel)
        panel_ly.setContentsMargins(28, 24, 28, 24)
        panel_ly.setSpacing(12)

        self.busy_overlay_label = QLabel("")
        self.busy_overlay_label.setObjectName("BusyOverlayLabel")
        self.busy_overlay_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_ly.addWidget(self.busy_overlay_label)

        self.busy_overlay_bar = QProgressBar()
        self.busy_overlay_bar.setObjectName("BusyOverlayBar")
        self.busy_overlay_bar.setRange(0, 100)
        self.busy_overlay_bar.setValue(0)
        self.busy_overlay_bar.setFixedSize(260, 10)
        self.busy_overlay_bar.setTextVisible(False)
        panel_ly.addWidget(self.busy_overlay_bar, 0, Qt.AlignmentFlag.AlignCenter)

        hint = QLabel(_t("busy_hint"))
        hint.setObjectName("BusyOverlayHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_ly.addWidget(hint)

        overlay_ly.addWidget(self.busy_panel, 0, Qt.AlignmentFlag.AlignCenter)
        overlay_ly.addStretch()
        self.busy_overlay.setVisible(False)
        self._position_busy_overlay()

    def _position_busy_overlay(self):
        if hasattr(self, "busy_overlay"):
            self.busy_overlay.setGeometry(self.rect())

    def resizeEvent(self, event):
        super().resizeEvent(event)
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
        if not checked:
            return
        tab_idx = self.stack.indexOf(self.fields_tab)
        item = self.sidebar.item(tab_idx)
        if item:
            item.setHidden(idx != 0)
        if idx != 0 and self.stack.currentIndex() == tab_idx:
            self.stack.setCurrentIndex(0)
            self.sidebar.setCurrentRow(0)

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
        """Re-read the deck list when the window is shown again; keeps the selection."""
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

    def _load_fields(self):
        """Rebuild the Fields tab: one group per note type used by the selected deck.

        Each field starts from the config remembered for its note type, so switching decks
        (or reopening the window) never loses per-note-type settings.
        """
        self._clear_field_widgets()
        dn = self._sel()
        if not dn:
            return
        counts = {}
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
            return
        for mid, cnt in sorted(counts.items(), key=lambda kv: -kv[1]):
            nt = mw.col.models.get(mid)
            if not nt:
                continue
            self._add_note_type_group(nt, cnt)

    def _add_note_type_group(self, nt, note_count):
        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        title = QLabel(_t("nt_header").format(name=nt["name"], n=note_count))
        title.setObjectName("NtHeader")
        title.setTextFormat(Qt.TextFormat.PlainText)
        hl.addWidget(title)
        hl.addStretch()
        if not _notetype_is_io(nt):
            reset = QPushButton(_t("nt_reset"))
            reset.setObjectName("SmallBtn")
            reset.setCursor(Qt.CursorShape.PointingHandCursor)
            reset.clicked.connect(lambda _=False, n=nt["name"]: self._reset_note_type(n))
            hl.addWidget(reset)
        self.fields_layout.insertWidget(self.fields_layout.count() - 1, header)
        self._nt_headers.append(header)
        if _notetype_is_io(nt):
            note = QLabel(_t("nt_io_auto"))
            note.setObjectName("HintLabel")
            note.setWordWrap(True)
            self.fields_layout.insertWidget(self.fields_layout.count() - 1, note)
            self._nt_headers.append(note)
            return
        saved = _store.get_fields(nt["name"])
        for fld in sorted(nt["flds"], key=lambda f: f["ord"]):
            w = FieldConfigWidget(
                fld["name"], is_front=_is_front_field(fld["name"]),
                nt_id=nt["id"], nt_name=nt["name"], config=saved.get(fld["name"]))
            w.changed.connect(lambda w=w: self._on_field_changed(w))
            self.fields_layout.insertWidget(self.fields_layout.count() - 1, w)
            self.field_widgets.append(w)

    def _on_field_changed(self, w):
        if self._loading:
            return
        _store.set_field(w.nt_name, w.field_name, w.get_config())
        self._schedule_save()

    def _reset_note_type(self, nt_name):
        _store.reset_fields(nt_name)
        self._schedule_save()
        self._load_fields()

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
            mode, "included" if "'Inter'" in info["stack"] else "skipped"))
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
        self._busy_val = (self._busy_val + 2) % 101
        if hasattr(self, "busy_overlay_bar"):
            self.busy_overlay_bar.setValue(self._busy_val)
        if hasattr(self, "busy_bar"):
            self.busy_bar.setValue(self._busy_val)
        
        self._spinner_idx = (self._spinner_idx + 1) % len(self._spinner_frames)
        frame = self._spinner_frames[self._spinner_idx]
        
        msg = self._base_busy_message or ""
        if hasattr(self, "busy_overlay_label"):
            self.busy_overlay_label.setText("{}   {}".format(frame, msg))

    def _set_busy_message(self, message):
        self._base_busy_message = message
        self.busy_label.setText(message)
        self.busy_wrap.setVisible(True)
        if hasattr(self, "busy_overlay"):
            self.busy_overlay_label.setText(message)
            self._position_busy_overlay()
            self.busy_overlay.setVisible(True)
            self.busy_overlay.raise_()
        QApplication.processEvents()

    def _begin_busy(self, message):
        if self._busy_depth == 0:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self._busy_val = 0
            self._spinner_idx = 0
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
        if not self._precheck():
            return
        try:
            self._begin_busy(_t("busy_preview"))
            logger.start("Preview")
            self._font_debug_logged_modes = set()
            self._active_export_theme_index = self.theme_radio.currentIndex()
            logger.log("Build: {}".format(EXPORT_BUILD))
            logger.log("Theme: {} ({})".format(self._theme_name(), self._theme_index()))
            html, card_ids = self._build_html(mode="preview")
            self._set_busy_message(_t("busy_opening"))
            fd, p = tempfile.mkstemp(suffix=".html", text=True)
            os.close(fd)
            with open(p, "w", encoding="utf-8") as f:
                f.write(html)
            logger.finish()
            self._save_debug_artifacts("preview", card_ids, html)
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))
            self._bring_to_front()
        except Exception as e:
            logger.error("Preview", e)
            logger.finish()
            showWarning(str(e))
        finally:
            self._end_busy(force=True)

    def _on_export(self):
        if not self._precheck():
            return
        dn = self._sel()
        short = self._safe_filename(dn.split("::")[-1] if "::" in dn else dn)
        uid = str(uuid.uuid4()).split('-')[0][:6]
        sp, _ = QFileDialog.getSaveFileName(
            self, _t("dlg_save_pdf"), "{}_{}.pdf".format(short, uid), _t("pdf_filter"))
        if not sp:
            return
        logger.start("Export")
        self._font_debug_logged_modes = set()
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
            "vendor_dir, html_path, pdf_path, font_json = sys.argv[1:5]\n"
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
            "    HTML(filename=html_path, base_url=os.path.dirname(html_path)).write_pdf(pdf_path)\n"
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
        if success:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            self._bring_to_front()
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
        """{note type id: {field name: config}} for the widgets currently shown."""
        fc = {}
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
            self.lang_combo.blockSignals(True)
            self._set_combo(self.lang_combo, self.lang_combo.findData(s["language"]))
            self.lang_combo.blockSignals(False)
            self.log_btn.setVisible(self.debug_cb.isChecked())
        finally:
            self._loading = was_loading

    def _connect_autosave(self):
        sched = self._schedule_save
        for rg in (self.theme_radio, self.width_radio, self.layout_radio, self.render_radio):
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
            if "'Inter'" in font else ""
        )
        page_numbers = self.page_numbers_cb.isChecked() and mode == "pdf"
        bottom_mm = max(top_mg, 12) if page_numbers else top_mg
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
            "break-inside:avoid;page-break-inside:avoid;overflow:hidden;display:block;width:100%}}"
            ".card.long-card{{break-inside:auto;page-break-inside:auto;overflow:visible}}"
            ".card.long-card .sec-q,.card.long-card .sec-a,.card.long-card .sec-x{{"
            "break-inside:auto;page-break-inside:auto;overflow:visible}}"
            ".cnum{{font-size:9px;font-weight:700;color:{mut};"
            "text-transform:uppercase;letter-spacing:.1em;padding:6px {padx}px 2px}}"
            ".sec-q,.sec-a,.sec-x{{overflow:hidden}}"
            ".sec-div{{height:0;border:none;border-top:1px solid {div};margin:0}}"
            ".fb{{padding:{padh}px {padx}px}}"
            ".fb+.fb{{border-top:1px solid {div}}}"
            ".fl{{font-size:{flsz}px;font-weight:600;color:{mut};"
            "text-transform:uppercase;letter-spacing:.06em;margin-bottom:1px}}"
            ".fv{{font-size:inherit;overflow:hidden}}"
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
            "img{{max-width:100%!important;max-height:{img_h}px;width:auto!important;"
            "height:auto!important;"
            "object-fit:contain;margin:3px 0;border-radius:4px;display:inline-block;"
            "vertical-align:top}}"
            "svg{{max-width:100%!important;height:auto!important;display:block;margin:3px 0}}"
            ".fv img:only-child{{margin:2px 0}}"
            "p:empty{{display:none}}div:empty{{display:none}}"
            ".rs{{padding:{padh}px {padx}px;overflow:hidden}}"
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
            pad=pad, padh=padh, padx=pad + 2,
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
                "background:{bg};{pnum}}}"
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
                     top_mm=top_mg, mg_mm=mg, bot_mm=bottom_mm, pnum=page_num_css)

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
                "@page{{size:{ps};margin:{mg}mm}}"
                "html,body{{background:{bg};padding:0}}"
                ".page{{box-shadow:none;margin:0;width:100%;min-height:auto;padding:0}}"
                ".page-break-marker{{display:none}}"
                "}}"
            ).format(content=content_css, pw=page_w_px, ph=page_h_px,
                     mg=mg_px, ps=ps, bg=t["body"])
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
                raw = re.sub(r"<(?!img\b|svg|/svg)[^>]+>", " ", raw)
                raw = re.sub(r"\s+", " ", raw).strip()
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
            return '<div class="fb" style="{}"><div class="fv">{}{}</div></div>'.format(
                fstyle(conf), label, val)

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
                version=_addon_version(),
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
            if mode == "pdf" and est > break_h_px * 0.45:
                return "card long-card"
            return "card"

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
            parts = ['<div class="{}"{}>'.format(card_class(est), ent["alt"])]
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
                if u["brk"] and n:
                    html.append('<div class="page-break"></div>')
                html.extend(u["parts"])
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
