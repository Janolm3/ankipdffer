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
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, showWarning

try:
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
except ImportError:
    from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineSettings


_STRINGS = {
    "en": {
        "window_title": "Anki → PDF",
        "menu_action": "Export Deck to PDF...",
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
        "dlg_save_pdf": "Save PDF",
        "pdf_filter": "PDF (*.pdf)",
        "msg_settings_saved": "Saved: {}",
        "msg_settings_err": "Save error: {}",
        "msg_no_settings": "No saved settings found.",
        "msg_settings_loaded": "Settings loaded.",
        "msg_settings_load_err": "Load error: {}",
        "msg_settings_reset": "Settings reset to defaults.",
        "msg_error": "Error.",
        "msg_pdf_saved": "PDF saved:\n{}",
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
    },
    "pl": {
        "window_title": "Anki → PDF",
        "menu_action": "Eksportuj Deck do PDF...",
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
        "dlg_save_pdf": "Zapisz PDF",
        "pdf_filter": "PDF (*.pdf)",
        "msg_settings_saved": "Zapisano: {}",
        "msg_settings_err": "Błąd zapisu ustawień: {}",
        "msg_no_settings": "Brak zapisanych ustawień.",
        "msg_settings_loaded": "Wczytano ustawienia.",
        "msg_settings_load_err": "Błąd wczytywania ustawień: {}",
        "msg_settings_reset": "Przywrócono ustawienia domyślne.",
        "msg_error": "Błąd.",
        "msg_pdf_saved": "PDF zapisano:\n{}",
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
    },
}

_lang = "en"
try:
    _sf = os.path.join(os.path.dirname(__file__), "settings.json")
    if os.path.exists(_sf):
        with open(_sf, encoding="utf-8") as _fh:
            _lang = json.load(_fh).get("language", "en")
except Exception:
    pass


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
        ly.setSpacing(2)
        self.group = QButtonGroup(self)
        self.buttons = []
        for i, label in enumerate(options):
            rb = QRadioButton(label)
            rb.setStyleSheet(
                "QRadioButton{spacing:3px;padding:0 4px}"
                "QRadioButton::indicator{width:12px;height:12px}"
            )
            if i == default:
                rb.setChecked(True)
            self.group.addButton(rb, i)
            self.buttons.append(rb)
            ly.addWidget(rb)
        ly.addStretch()
        self.setLayout(ly)

    def currentIndex(self):
        return self.group.checkedId()

    def setCurrentIndex(self, idx):
        if 0 <= idx < len(self.buttons):
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


class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)

    def javaScriptConsoleMessage(self, level, msg, line, src):
        logger.log("JS [{}] L{}: {}".format(level, line, msg))


class FieldConfigWidget(QWidget):
    def __init__(self, field_name, is_front=False, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        root = QVBoxLayout()
        root.setContentsMargins(8, 4, 8, 4)
        root.setSpacing(0)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.export_cb = QCheckBox()
        self.export_cb.setChecked(True)
        row.addWidget(self.export_cb)
        self.name_label = QLabel("<b>{}</b>".format(field_name))
        self.name_label.setMinimumWidth(120)
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
        self.bold_cb.setStyleSheet("font-weight:bold")
        row.addWidget(self.bold_cb)
        self.label_cb = QCheckBox(_t("field_lbl_label"))
        self.label_cb.setChecked(not is_front)
        row.addWidget(self.label_cb)
        row.addStretch()
        self.adv_btn = QPushButton("\u22ef")
        self.adv_btn.setFixedSize(26, 26)
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
        self.italic_cb.setStyleSheet("font-style:italic")
        ap.addWidget(self.italic_cb)
        self.underline_cb = QCheckBox("U")
        self.underline_cb.setStyleSheet("text-decoration:underline")
        ap.addWidget(self.underline_cb)
        ap.addStretch()
        self.adv_panel.setLayout(ap)
        root.addWidget(self.adv_panel)
        self.setLayout(root)

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


PAGE_SIZES = {"A4": (210, 297), "Letter": (216, 279), "A3": (297, 420), "A5": (148, 210)}

CARD_WIDTH_PRESETS = [
    ("Wąska — 520px", 520),
    ("Średnia — 680px", 680),
    ("Szeroka — 860px", 860),
    ("Pełna", 0),
    ("Własna…", -1),
]

FONT_OPTIONS = [
    ("System", "-apple-system,BlinkMacSystemFont,'Inter','Segoe UI',Roboto,Helvetica,Arial,sans-serif"),
    ("Inter", "'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif"),
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

DEFAULT_SETTINGS = {
    "theme": 0,
    "font": 0,
    "font_size": 13,
    "width": 1,
    "custom_width": 800,
    "layout": 1,
    "render": 0,
    "show_title": True,
    "card_numbers": False,
    "zebra": False,
    "page": 0,
    "margins": 15,
    "top_margin": 10,
    "padding": 12,
    "min_gap": 8,
    "line_height": 1.40,
    "max_img": 240,
    "strip_html": False,
    "card_style": 0,
    "grid": False,
    "language": "en",
    "debug": False,
    "high_contrast": False,
}


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
        self.field_widgets = []
        self._all_decks = []

        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            w = max(700, min(int(sg.width() * 0.52), 960))
            h = max(520, min(int(sg.height() * 0.68), 740))
            self.resize(w, h)
            self.setMinimumSize(600, 440)
        else:
            self.resize(820, 640)
            self.setMinimumSize(600, 440)

        root = QVBoxLayout()
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

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
        deck_group.setLayout(dg)
        root.addWidget(deck_group)

        content_frame = QFrame()
        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(150)
        self.sidebar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sidebar.setStyleSheet("""
            QListWidget#Sidebar {
                background: transparent;
                border: none;
                border-right: 1px solid rgba(128, 128, 128, 0.2);
                outline: none;
                padding-top: 8px;
            }
            QListWidget#Sidebar::item {
                padding: 10px 14px;
                margin: 2px 8px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }
            QListWidget#Sidebar::item:selected {
                background: rgba(59, 130, 246, 0.15);
                color: #3b82f6;
                font-weight: bold;
            }
            QListWidget#Sidebar::item:hover:!selected {
                background: rgba(128, 128, 128, 0.1);
            }
        """)
        content_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack, 1)

        basic = QWidget()
        bl = QVBoxLayout(basic)
        bl.setContentsMargins(16, 20, 16, 20)
        bl.setSpacing(16)

        r_theme = QHBoxLayout()
        r_theme.addWidget(QLabel(_t("lbl_theme")))
        self.theme_radio = InlineRadioGroup(
            [_t("theme_light"), _t("theme_dark"), _t("theme_pro")], default=0)
        r_theme.addWidget(self.theme_radio)
        r_theme.addStretch()
        bl.addLayout(r_theme)

        r_font = QHBoxLayout()
        r_font.addWidget(QLabel(_t("lbl_font")))
        self.font_combo = NoScrollComboBox()
        self.font_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for name, _ in FONT_OPTIONS:
            self.font_combo.addItem(name)
        self.font_combo.setCurrentIndex(0)
        self.font_combo.setMinimumWidth(150)
        r_font.addWidget(self.font_combo)
        r_font.addSpacing(14)
        r_font.addWidget(QLabel(_t("lbl_size")))
        self.fontsize_spin = QSpinBox()
        self.fontsize_spin.setRange(10, 24)
        self.fontsize_spin.setValue(13)
        self.fontsize_spin.setSuffix(" px")
        r_font.addWidget(self.fontsize_spin)
        r_font.addStretch()
        bl.addLayout(r_font)

        r_width = QHBoxLayout()
        r_width.addWidget(QLabel(_t("lbl_width")))
        self.width_radio = InlineRadioGroup([
            _t("width_narrow"), _t("width_medium"), _t("width_wide"),
            _t("width_full"), _t("width_custom"),
        ], default=1)
        r_width.addWidget(self.width_radio)
        self.width_spin = NoScrollSpinBox()
        self.width_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.width_spin.setRange(300, 3000)
        self.width_spin.setValue(800)
        self.width_spin.setSuffix(" px")
        self.width_spin.setVisible(False)
        r_width.addWidget(self.width_spin)
        self.width_radio.group.idToggled.connect(self._on_width_radio_changed)
        r_width.addStretch()
        bl.addLayout(r_width)

        r_layout = QHBoxLayout()
        r_layout.addWidget(QLabel(_t("lbl_layout")))
        self.layout_radio = InlineRadioGroup(
            [_t("layout_standard"), _t("layout_compact")], default=1)
        r_layout.addWidget(self.layout_radio)
        r_layout.addStretch()
        bl.addLayout(r_layout)

        r_src = QHBoxLayout()
        r_src.addWidget(QLabel(_t("lbl_source")))
        self.render_radio = InlineRadioGroup(
            [_t("source_fields"), _t("source_cards")], default=0)
        self.render_radio.group.idToggled.connect(self._on_render_radio_changed)
        r_src.addWidget(self.render_radio)
        r_src.addStretch()
        bl.addLayout(r_src)

        r_cb = QHBoxLayout()
        self.show_title_cb = QCheckBox(_t("cb_title"))
        self.show_title_cb.setChecked(True)
        r_cb.addWidget(self.show_title_cb)
        self.card_numbers_cb = QCheckBox(_t("cb_numbers"))
        r_cb.addWidget(self.card_numbers_cb)
        self.zebra_cb = QCheckBox(_t("cb_zebra"))
        r_cb.addWidget(self.zebra_cb)
        self.high_contrast_cb = QCheckBox(_t("cb_high_contrast"))
        r_cb.addWidget(self.high_contrast_cb)
        r_cb.addStretch()
        bl.addLayout(r_cb)

        bl.addStretch()
        self.stack.addWidget(basic)
        self.sidebar.addItem(_t("tab_basic"))

        adv = QWidget()
        avl = QVBoxLayout(adv)
        avl.setContentsMargins(16, 20, 16, 20)
        avl.setSpacing(16)
        pg = QHBoxLayout()

        def _spin(label, attr, lo, hi, val, sfx):
            v = QVBoxLayout()
            v.addWidget(QLabel(label))
            sp = NoScrollSpinBox()
            sp.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            sp.setRange(lo, hi)
            sp.setValue(val)
            sp.setSuffix(sfx)
            setattr(self, attr, sp)
            v.addWidget(sp)
            pg.addLayout(v)

        v0 = QVBoxLayout()
        v0.addWidget(QLabel(_t("lbl_page")))
        self.page_combo = QComboBox()
        self.page_combo.addItems(["A4", "Letter", "A3", "A5"])
        v0.addWidget(self.page_combo)
        pg.addLayout(v0)
        _spin(_t("lbl_margins"), "margin_spin", 5, 40, 15, " mm")
        _spin(_t("lbl_top_margin"), "top_margin_spin", 0, 40, 10, " mm")
        _spin(_t("lbl_padding"), "padding_spin", 2, 50, 12, " px")
        _spin(_t("lbl_gap"), "gap_spin", 0, 80, 8, " px")

        v1 = QVBoxLayout()
        v1.addWidget(QLabel(_t("lbl_lineheight")))
        self.lh_spin = NoScrollDoubleSpinBox()
        self.lh_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.lh_spin.setRange(1.0, 2.5)
        self.lh_spin.setValue(1.40)
        self.lh_spin.setSingleStep(0.05)
        v1.addWidget(self.lh_spin)
        pg.addLayout(v1)
        _spin(_t("lbl_maximg"), "img_h_spin", 60, 800, 240, " px")
        avl.addLayout(pg)

        ra = QHBoxLayout()
        self.strip_html_cb = QCheckBox(_t("cb_strip_html"))
        ra.addWidget(self.strip_html_cb)
        ra.addSpacing(14)
        ra.addWidget(QLabel(_t("lbl_card_style")))
        self.card_style_combo = QComboBox()
        self.card_style_combo.addItems([
            _t("style_rounded"), _t("style_sharp"), _t("style_separator"),
            _t("style_double"), _t("style_none"),
        ])
        ra.addWidget(self.card_style_combo)
        ra.addStretch()
        avl.addLayout(ra)
        avl.addStretch()
        self.stack.addWidget(adv)
        self.sidebar.addItem(_t("tab_advanced"))

        self.fields_tab = QWidget()
        fl = QVBoxLayout(self.fields_tab)
        fl.setContentsMargins(12, 16, 12, 16)
        fl.setSpacing(10)
        hint = QLabel(_t("fields_hint"))
        hint.setStyleSheet("color:#64748b;font-size:11px;padding:0 4px 4px")
        hint.setWordWrap(True)
        fl.addWidget(hint)
        self.fields_scroll = QScrollArea()
        self.fields_scroll.setWidgetResizable(True)
        self.fields_container = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setContentsMargins(2, 2, 2, 2)
        self.fields_layout.setSpacing(1)
        self.fields_layout.addStretch()
        self.fields_scroll.setWidget(self.fields_container)
        fl.addWidget(self.fields_scroll)
        self.stack.addWidget(self.fields_tab)
        self.sidebar.addItem(_t("tab_fields"))

        settings_tab = QWidget()
        stl = QVBoxLayout(settings_tab)
        stl.setSpacing(16)
        stl.setContentsMargins(16, 20, 16, 20)

        preset_group = QGroupBox(_t("grp_settings"))
        preset_ly = QVBoxLayout()
        preset_ly.setSpacing(8)
        preset_row1 = QHBoxLayout()
        self.save_settings_btn = QPushButton(_t("btn_save_settings"))
        self.save_settings_btn.setMinimumHeight(30)
        self.save_settings_btn.clicked.connect(self._save_settings)
        preset_row1.addWidget(self.save_settings_btn)
        self.load_settings_btn = QPushButton(_t("btn_load_settings"))
        self.load_settings_btn.setMinimumHeight(30)
        self.load_settings_btn.clicked.connect(self._load_settings)
        preset_row1.addWidget(self.load_settings_btn)
        preset_row1.addStretch()
        preset_ly.addLayout(preset_row1)
        preset_row2 = QHBoxLayout()
        self.reset_btn = QPushButton(_t("btn_reset_settings"))
        self.reset_btn.setMinimumHeight(30)
        self.reset_btn.clicked.connect(self._reset_settings)
        preset_row2.addWidget(self.reset_btn)
        preset_row2.addStretch()
        preset_ly.addLayout(preset_row2)
        self.settings_info = QLabel("")
        self.settings_info.setStyleSheet("color:#64748b;font-size:11px")
        self.settings_info.setWordWrap(True)
        preset_ly.addWidget(self.settings_info)
        preset_group.setLayout(preset_ly)
        stl.addWidget(preset_group)

        lang_group = QGroupBox(_t("grp_language"))
        lang_ly = QHBoxLayout()
        self.lang_radio = InlineRadioGroup(["English", "Polski"],
                                           default=0 if _lang == "en" else 1)
        lang_ly.addWidget(self.lang_radio)
        lang_hint = QLabel(_t("lang_hint"))
        lang_hint.setStyleSheet("color:#64748b;font-size:11px")
        lang_ly.addWidget(lang_hint)
        lang_ly.addStretch()
        lang_group.setLayout(lang_ly)
        stl.addWidget(lang_group)

        dbg_group = QGroupBox(_t("grp_debug"))
        dbg_ly = QHBoxLayout()
        self.debug_cb = QCheckBox(_t("cb_debug"))
        dbg_ly.addWidget(self.debug_cb)
        self.log_btn = QPushButton(_t("btn_logs"))
        self.log_btn.setMinimumHeight(30)
        self.log_btn.setVisible(False)
        self.log_btn.clicked.connect(self._show_logs)
        dbg_ly.addWidget(self.log_btn)
        dbg_ly.addStretch()
        dbg_group.setLayout(dbg_ly)
        stl.addWidget(dbg_group)
        self.debug_cb.toggled.connect(self.log_btn.setVisible)

        stl.addStretch()
        self.stack.addWidget(settings_tab)
        self.sidebar.addItem(_t("tab_settings"))
        
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

        root.addWidget(content_frame)

        bottom = QHBoxLayout()
        bottom.setSpacing(6)
        bottom.addStretch()

        self.grid_cb = QCheckBox(_t("cb_grid"))
        bottom.addWidget(self.grid_cb)
        bottom.addSpacing(6)

        _btn_base = (
            "QPushButton{{"
            "border:1px solid {brd};background:{bg};color:{fg};"
            "border-radius:6px;padding:7px 18px;font-size:13px;"
            "font-weight:500;letter-spacing:0.01em}}"
            "QPushButton:hover{{background:{hover}}}"
            "QPushButton:pressed{{background:{pressed}}}"
            "QPushButton:disabled{{opacity:0.5}}"
        )

        self.legacy_btn = QPushButton(_t("btn_legacy"))
        self.legacy_btn.setMinimumHeight(34)
        self.legacy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.legacy_btn.setStyleSheet(_btn_base.format(
            brd="#d0d5dd", bg="#ffffff", fg="#344054",
            hover="#f9fafb", pressed="#f2f4f7"))
        self.legacy_btn.clicked.connect(self._on_legacy)
        bottom.addWidget(self.legacy_btn)

        self.preview_btn = QPushButton(_t("btn_preview"))
        self.preview_btn.setMinimumHeight(34)
        self.preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_btn.setStyleSheet(_btn_base.format(
            brd="#d0d5dd", bg="#ffffff", fg="#344054",
            hover="#f9fafb", pressed="#f2f4f7"))
        self.preview_btn.clicked.connect(self._on_preview)
        bottom.addWidget(self.preview_btn)

        self.export_btn = QPushButton(_t("btn_export"))
        self.export_btn.setMinimumHeight(34)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setStyleSheet(_btn_base.format(
            brd="#3b82f6", bg="#3b82f6", fg="#ffffff",
            hover="#60a5fa", pressed="#2563eb"))
        self.export_btn.clicked.connect(self._on_export)
        bottom.addWidget(self.export_btn)
        root.addLayout(bottom)
        self.setLayout(root)

        self._populate_decks()
        self.deck_combo.currentIndexChanged.connect(self._on_deck_changed)
        self.subdeck_combo.currentIndexChanged.connect(self._on_subdeck_changed)
        self._try_autoload_settings()

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

    def _populate_decks(self):
        self._all_decks = sorted(mw.col.decks.all_names_and_ids(), key=lambda d: d.name)
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
        cur = mw.col.decks.current()
        if cur:
            i = self.deck_combo.findText(cur["name"].split("::")[0])
            if i >= 0:
                self.deck_combo.setCurrentIndex(i)
        self._on_deck_changed()

    def _on_deck_changed(self):
        rn = self.deck_combo.currentText()
        if not rn:
            return
        self.subdeck_combo.blockSignals(True)
        self.subdeck_combo.clear()
        self.subdeck_combo.addItem(_t("entire_deck"), rn)
        pfx = rn + "::"
        for d in self._all_decks:
            if d.name.startswith(pfx):
                self.subdeck_combo.addItem(d.name[len(pfx):], d.name)
        self.subdeck_combo.blockSignals(False)
        cur = mw.col.decks.current()
        if cur and cur["name"].startswith(pfx):
            i = self.subdeck_combo.findData(cur["name"])
            if i >= 0:
                self.subdeck_combo.setCurrentIndex(i)
        self._on_subdeck_changed()

    def _sel(self):
        d = self.subdeck_combo.currentData()
        return d if d else self.deck_combo.currentText()

    def _on_subdeck_changed(self):
        self._load_fields()

    def _load_fields(self):
        for w in self.field_widgets:
            w.setParent(None)
            w.deleteLater()
        self.field_widgets.clear()
        dn = self._sel()
        if not dn:
            return
        cids = mw.col.find_cards('"deck:{}"'.format(dn))
        if not cids:
            return
        chunk = 500
        nids = set()
        for i in range(0, len(cids), chunk):
            s = ",".join(str(c) for c in cids[i:i + chunk])
            nids.update(mw.col.db.list("SELECT nid FROM cards WHERE id IN ({})".format(s)))
        mids = set()
        nl = list(nids)
        for i in range(0, len(nl), chunk):
            s = ",".join(str(n) for n in nl[i:i + chunk])
            mids.update(mw.col.db.list("SELECT mid FROM notes WHERE id IN ({})".format(s)))
        ordered = []
        seen = set()
        for mid in mids:
            m = mw.col.models.get(mid)
            if m:
                for f in m["flds"]:
                    if f["name"] not in seen:
                        ordered.append((f["ord"], f["name"]))
                        seen.add(f["name"])
        ordered.sort(key=lambda x: x[0])
        kw = ["pytanie", "question", "front", "przod", "zagadnienie", "text", "tekst", "header", "image"]
        for _, fn in ordered:
            is_f = any(k in fn.lower() for k in kw)
            w = FieldConfigWidget(fn, is_front=is_f)
            self.fields_layout.insertWidget(self.fields_layout.count() - 1, w)
            self.field_widgets.append(w)

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

    def _get_page_dims(self):
        return PAGE_SIZES.get(self.page_combo.currentText(), (210, 297))

    def _set_btns(self, on):
        self.legacy_btn.setEnabled(on)
        self.preview_btn.setEnabled(on)
        self.export_btn.setEnabled(on)

    def _bring_to_front(self):
        QTimer.singleShot(300, lambda: (self.raise_(), self.activateWindow()))

    def _save_debug_artifacts(self, mode, card_ids, html_output):
        if not self.debug_cb.isChecked():
            return
        desktop = os.path.expanduser("~/Desktop")
        short = self._sel().split("::")[-1]
        ts = datetime.datetime.now().strftime("%H%M%S")
        html_path = os.path.join(desktop, "anki_debug_{}_{}.html".format(short, ts))
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_output)
        logger.save(os.path.join(desktop, "anki_pdf_log.txt"))

    def _on_legacy(self):
        try:
            logger.start("Legacy")
            html, card_ids = self._build_html(mode="legacy")
            _, p = tempfile.mkstemp(suffix=".html", text=True)
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

    def _on_preview(self):
        try:
            logger.start("Preview")
            html, card_ids = self._build_html(mode="preview")
            _, p = tempfile.mkstemp(suffix=".html", text=True)
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

    def _on_export(self):
        dn = self._sel()
        short = dn.split("::")[-1] if "::" in dn else dn
        uid = str(uuid.uuid4()).split('-')[0][:6]
        sp, _ = QFileDialog.getSaveFileName(
            self, _t("dlg_save_pdf"), "{}_{}.pdf".format(short, uid), _t("pdf_filter"))
        if not sp:
            return
        logger.start("Export")
        self._set_btns(False)
        self.export_btn.setText(_t("generating"))
        try:
            QApplication.processEvents()
            html, card_ids = self._build_html(mode="pdf")
            _, self.temp_html_path = tempfile.mkstemp(suffix=".html", text=True)
            with open(self.temp_html_path, "w", encoding="utf-8") as f:
                f.write(html)
            self._save_debug_artifacts("pdf", card_ids, html)
            self.page = CustomWebEnginePage()
            try:
                self.page.settings().setAttribute(
                    QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
            except AttributeError:
                pass
            _bg_colors = ["#ffffff", "#111111", "#f8fafc"]
            _bg = _bg_colors[self.theme_radio.currentIndex()]
            try:
                self.page.setBackgroundColor(QColor(_bg))
            except Exception:
                pass
            self.page.loadFinished.connect(lambda ok: self._loaded(ok, sp))
            self.page.load(QUrl.fromLocalFile(self.temp_html_path))
        except Exception as e:
            logger.error("Export", e)
            logger.finish()
            self._save_debug_log()
            showWarning(str(e))
            self._reset()

    def _loaded(self, ok, path):
        if not ok:
            logger.error("Load fail")
            logger.finish()
            self._save_debug_log()
            showWarning(_t("msg_error"))
            self._reset()
            return

        self._do_print(path)

    def _do_print(self, path):
        self.export_btn.setText(_t("printing"))
        try:
            from PyQt6.QtCore import QMarginsF
            from PyQt6.QtGui import QPageLayout, QPageSize
            ps_map = {
                "A4": QPageSize.PageSizeId.A4,
                "Letter": QPageSize.PageSizeId.Letter,
                "A3": QPageSize.PageSizeId.A3,
                "A5": QPageSize.PageSizeId.A5,
            }
            size = QPageSize(ps_map.get(self.page_combo.currentText(), QPageSize.PageSizeId.A4))
            margins = QMarginsF(0, 0, 0, 0)
            layout = QPageLayout(size, QPageLayout.Orientation.Portrait, margins,
                                 QPageLayout.Unit.Millimeter)
            self.page.pdfPrintingFinished.connect(self._printed)
            self.page.printToPdf(path, layout)
        except (ImportError, AttributeError):
            self.page.pdfPrintingFinished.connect(self._printed)
            self.page.printToPdf(path)

    def _printed(self, path, success):
        if success and os.path.exists(path):
            logger.log("PDF: {} B".format(os.path.getsize(path)))
        logger.finish()
        self._save_debug_log()
        self._reset()
        if self.temp_html_path:
            try:
                os.remove(self.temp_html_path)
            except OSError:
                pass
        if success:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            self._bring_to_front()
            showInfo(_t("msg_pdf_saved").format(path))

    def _save_debug_log(self):
        if self.debug_cb.isChecked():
            logger.save(os.path.join(os.path.expanduser("~/Desktop"), "anki_pdf_log.txt"))

    def _reset(self):
        self.export_btn.setText(_t("btn_export"))
        self._set_btns(True)

    def _collect_fc(self):
        fc = {}
        for w in self.field_widgets:
            fc[w.field_name] = w.get_config()
        return fc

    @staticmethod
    def _settings_path():
        return os.path.join(os.path.dirname(__file__), "settings.json")

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
            "language": "en" if self.lang_radio.currentIndex() == 0 else "pl",
            "debug": self.debug_cb.isChecked(),
            "high_contrast": self.high_contrast_cb.isChecked(),
        }

    def _apply_settings(self, s):
        self.theme_radio.setCurrentIndex(s.get("theme", 0))
        self.font_combo.setCurrentIndex(s.get("font", 0))
        self.fontsize_spin.setValue(s.get("font_size", 13))
        self.width_radio.setCurrentIndex(s.get("width", 1))
        self.width_spin.setValue(s.get("custom_width", 800))
        self.layout_radio.setCurrentIndex(s.get("layout", 1))
        self.render_radio.setCurrentIndex(s.get("render", 0))
        self.show_title_cb.setChecked(s.get("show_title", True))
        self.card_numbers_cb.setChecked(s.get("card_numbers", False))
        self.zebra_cb.setChecked(s.get("zebra", False))
        self.page_combo.setCurrentIndex(s.get("page", 0))
        self.margin_spin.setValue(s.get("margins", 15))
        self.top_margin_spin.setValue(s.get("top_margin", 10))
        self.padding_spin.setValue(s.get("padding", 12))
        self.gap_spin.setValue(s.get("min_gap", 4))
        self.lh_spin.setValue(s.get("line_height", 1.40))
        self.img_h_spin.setValue(s.get("max_img", 240))
        self.strip_html_cb.setChecked(s.get("strip_html", False))
        self.card_style_combo.setCurrentIndex(s.get("card_style", 0))
        self.grid_cb.setChecked(s.get("grid", False))
        self.lang_radio.setCurrentIndex(0 if s.get("language", "en") == "en" else 1)
        self.debug_cb.setChecked(s.get("debug", False))
        self.high_contrast_cb.setChecked(s.get("high_contrast", False))

    def _save_settings(self):
        try:
            s = self._get_all_settings()
            with open(self._settings_path(), "w", encoding="utf-8") as f:
                json.dump(s, f, indent=2, ensure_ascii=False)
            self.settings_info.setText(_t("msg_settings_saved").format(self._settings_path()))
        except Exception as e:
            showWarning(_t("msg_settings_err").format(e))

    def _load_settings(self):
        p = self._settings_path()
        if not os.path.exists(p):
            showInfo(_t("msg_no_settings"))
            return
        try:
            with open(p, "r", encoding="utf-8") as f:
                s = json.load(f)
            self._apply_settings(s)
            self.settings_info.setText(_t("msg_settings_loaded"))
        except Exception as e:
            showWarning(_t("msg_settings_load_err").format(e))

    def _try_autoload_settings(self):
        p = self._settings_path()
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    s = json.load(f)
                self._apply_settings(s)
            except Exception:
                pass

    def _reset_settings(self):
        self._apply_settings(DEFAULT_SETTINGS)
        p = self._settings_path()
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass
        self.settings_info.setText(_t("msg_settings_reset"))

    def _build_html(self, mode="pdf"):
        deck_name = self._sel()
        media_dir = mw.col.media.dir()
        render_mode = self.render_radio.currentIndex()
        fc = self._collect_fc()
        compact = self.layout_radio.currentIndex() == 1

        fi = self.font_combo.currentIndex()
        font = FONT_OPTIONS[fi][1] if fi < len(FONT_OPTIONS) else FONT_OPTIONS[0][1]
        bsz = self.fontsize_spin.value()
        pad = self.padding_spin.value()
        padh = max(4, pad - 4)
        min_gap = self.gap_spin.value()
        css_gap = min_gap
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

        themes = [
            dict(body="#ffffff", card="#ffffff", brd="#e5e7eb", txt="#111827",
                 mut="#9ca3af", acc="#111827", div="#e5e7eb", alt="#f9fafb"),
            dict(body="#111111", card="#1a1a1a", brd="#2a2a2a", txt="#e5e5e5",
                 mut="#666666", acc="#ffffff", div="#2a2a2a", alt="#151515"),
            dict(body="#f8fafc", card="#ffffff", brd="#bfdbfe", txt="#0f172a",
                 mut="#64748b", acc="#1d4ed8", div="#bfdbfe", alt="#eff6ff"),
        ]
        t = themes[self.theme_radio.currentIndex()]
        grid_mode = self.grid_cb.isChecked() if mode == "legacy" else False

        cs = self.card_style_combo.currentIndex()
        card_styles = [
            "border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.08);border:1px solid {};".format(t["brd"]),
            "border-radius:0;border:1px solid {};".format(t["brd"]),
            "border:none;border-bottom:1px solid {};border-radius:0;".format(t["brd"]),
            "border-radius:4px;border:2px double {};".format(t["mut"]),
            "border:none;border-radius:0;box-shadow:none;",
        ]
        card_extra = card_styles[cs]

        bg_map = ["__auto__", "#ffffff", "#f8f9fa", "#f0f4ff", "#fffde7", "#f0fdf4", "#fff5f5", "#f5f3ff"]
        sz_map = ["0.8em", "1em", "1.15em", "1.4em"]
        cl_map = ["inherit", "#9ca3af", "#ef4444", "#3b82f6", "#22c55e", "#f97316", "#8b5cf6"]
        al_map = ["left", "center", "justify", "right"]

        display_title = deck_name.split("::")[-1] if "::" in deck_name else deck_name
        label_sz = max(8, bsz - 4)

        if card_max_w > 0:
            content_max_w_css = ".page-content{{max-width:{mw}px;margin:0 auto}}".format(mw=card_max_w)
        else:
            content_max_w_css = ""

        sanitise_css = (
            ".fv [style*='background']{{background:transparent!important}}"
            ".fv [style*='Background']{{background:transparent!important}}"
            ".fv .nightMode,.fv .night_mode,.fv .nightmode{{all:unset!important}}"
            ".fv [style*='color:white']{{color:inherit!important}}"
            ".fv [style*='color:#fff']{{color:inherit!important}}"
            ".fv [style*='color: white']{{color:inherit!important}}"
            ".fv [style*='width'][style*='height']{{max-width:100%!important;height:auto!important}}"
            ".fv style{{display:none!important}}"
            ".rs [style*='background']{{background:transparent!important}}"
            ".rs .nightMode,.rs .night_mode,.rs .nightmode{{all:unset!important}}"
            ".rs [style*='color:white']{{color:inherit!important}}"
            ".rs [style*='color:#fff']{{color:inherit!important}}"
        )

        io_css_str = (
            ".io-wrap{position:relative;display:inline-block;line-height:0;max-width:100%}"
            ".io-wrap img{display:block;max-width:100%!important;height:auto!important;"
            "max-height:none!important;border-radius:0}"
            ".io-wrap svg{position:absolute;top:0;left:0;"
            "width:100%!important;height:100%!important}"
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

        c_padh = max(3, padh * 2 // 3)
        if compact:
            c_padx = max(5, (pad + 2) * 2 // 3)
            compact_css = (
                "h1.doc-title{{margin-top:0!important}}"
                "body.compact .card{{box-shadow:none;border-radius:4px}}"
                "body.compact .fb{{padding:{cph}px {cpx}px}}"
                "body.compact .rs{{padding:{cph}px {cpx}px}}"
                "body.compact .cnum{{padding:3px {cpx}px 1px}}"
                "body.compact .fv p{{margin:0 0 .1em}}"
                "body.compact .fv ul,body.compact .fv ol{{margin:.1em 0}}"
                "body.compact .fv li{{margin-bottom:0}}"
                "body.compact img{{margin:2px 0}}"
            ).format(cph=c_padh, cpx=c_padx, top_mg=top_mg)
        else:
            compact_css = ""

        content_css = (
            "@import url('https://fonts.googleapis.com/css2?"
            "family=Inter:wght@400;500;600;700;800&display=swap');"
            "*,*::before,*::after{{font-family:{font}!important;box-sizing:border-box!important;"
            "-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}}"
            "html{{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}}"
            "body{{color:{txt};font-size:{bsz}px;line-height:{lh};"
            "-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;"
            "word-wrap:break-word;overflow-wrap:break-word;"
            "-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}}"
            "h1.doc-title{{text-align:center;font-size:{h1sz}px;font-weight:800;"
            "color:{acc};margin:{top_mgpx}px 0 2px;padding-top:0;letter-spacing:-.03em}}"
            ".sub{{text-align:center;color:{mut};font-size:{subsz}px;"
            "font-weight:500;margin:0 0 {subgap}px;letter-spacing:-.01em}}"
            ".card{{{card_extra}background:{card};margin-bottom:{gap}px!important;"
            "page-break-inside:avoid;overflow:hidden;display:block;width:100%}}"
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
            "{content_max_w}"
            "{sanitise}"
            "{compact_overrides}"
            "{io_css}"
            "{hc_css}"
        ).format(
            font=font, txt=t["txt"], bsz=bsz, lh=lh,
            h1sz=bsz + 6, acc=t["acc"], mut=t["mut"], subsz=bsz - 2, subgap=min_gap + 2,
            card_extra=card_extra, card=t["card"], gap=css_gap,
            top_mgpx=int(top_mg_px),
            pad=pad, padh=padh, padx=pad + 2,
            div=t["div"], flsz=label_sz, brd=t["brd"], img_h=img_h,
            content_max_w=content_max_w_css,
            sanitise=sanitise_css,
            compact_overrides=compact_css,
            io_css=io_css_str,
            hc_css=hc_css_str,
        )

        if mode == "pdf":
            wrapper_css = (
                "@page{{size:{ps};margin:0}}"
                "{content}"
                "html{{background-color:{bg}!important;min-height:100%;"
                "-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}}"
                "body{{background-color:{bg}!important;margin:0;padding:0;"
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
                "background:{bg};padding:{mg:.0f}px;padding-top:{top_mg:.0f}px;"
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
                     mg=mg_px, top_mg=top_mg_px, ps=ps, bg=t["body"])
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
        body_cls = ' class="{}"'.format(" ".join(body_classes)) if body_classes else ''

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
                '<body{cls} style="background-color:{bg};margin:0;'
                'padding:{top_mg}mm {mg}mm {mg}mm {mg}mm;box-sizing:border-box;'
                '-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important">'
                '<div style="position:fixed;top:0;left:0;right:0;bottom:0;'
                'background-color:{bg};z-index:0;'
                '-webkit-print-color-adjust:exact!important;'
                'print-color-adjust:exact!important"></div>'
            ).format(cls=body_cls, bg=_bg, mg=mg, top_mg=top_mg)
            html = [html_open, wrapper_css, body_open]
        else:
            html = [
                "<!DOCTYPE html><html><head><meta charset='utf-8'><style>",
                wrapper_css,
                "</style></head><body{}>".format(body_cls),
            ]

        if mode == "preview":
            html.append('<div class="page"><div class="page-content">')
        elif mode == "legacy":
            html.append('<div class="page-content">')
        else:
            html.append('<div class="page-content">')

        if show_title:
            html.append('<h1 class="doc-title">{}</h1>'.format(display_title))
            if "::" in deck_name:
                html.append('<div class="sub">{}</div>'.format(
                    deck_name.replace("::", " &rsaquo; ")))

        card_ids = mw.col.find_cards('"deck:{}"'.format(deck_name))
        logger.log("Kart: {}".format(len(card_ids)))

        img_ok = [0]
        img_fail = [0]

        def b64(fn):
            clean = urllib.parse.unquote(fn)
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

        img_re = re.compile(r'src=(["\'])(?!http|data:)([^"\']+)\1')
        xlink_re = re.compile(r'xlink:href=(["\'])(?!http|data:)([^"\']+)\1')

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

        def sanitise_html(raw):
            if not raw:
                return raw
            raw, svgs = _protect_svg(raw)
            raw = re.sub(r"<style[^>]*>.*?</style>", "", raw, flags=re.DOTALL)
            raw = re.sub(r"<script[^>]*>.*?</script>", "", raw, flags=re.DOTALL)
            raw = re.sub(r"<meta[^>]*>", "", raw, flags=re.IGNORECASE)
            raw = re.sub(r"<title[^>]*>.*?</title>", "", raw, flags=re.DOTALL | re.IGNORECASE)
            raw = re.sub(r"<h1[^>]*>(.*?)</h1>", r"<p><strong>\1</strong></p>",
                         raw, flags=re.DOTALL | re.IGNORECASE)
            raw = re.sub(r"<h2[^>]*>(.*?)</h2>", r"<p><strong>\1</strong></p>",
                         raw, flags=re.DOTALL | re.IGNORECASE)
            raw = re.sub(
                r'(style="[^"]*?)background(?:-color)?:\s*(?:#[0-3][0-9a-fA-F]{2,5}|'
                r'rgb\(\s*[0-4]\d|black|#000[^"]*)',
                r'\1background:transparent', raw, flags=re.IGNORECASE)
            raw = re.sub(
                r'(style="[^"]*?)color:\s*(?:white|#fff(?:fff)?)\b',
                r'\1color:inherit', raw, flags=re.IGNORECASE)
            raw = re.sub(
                r'width:\s*(\d{4,})px',
                lambda m: "width:100%" if int(m.group(1)) > 800 else m.group(0), raw)
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
            label = '<div class="fl">{}</div>'.format(fname) if conf["label"] else ""
            return '<div class="fb" style="{}"><div class="fv">{}{}</div></div>'.format(
                fstyle(conf), label, val)

        def clean_rendered(raw_html):
            raw_html, svgs = _protect_svg(raw_html)
            c = re.sub(r"<style[^>]*>.*?</style>", "", raw_html, flags=re.DOTALL)
            c = re.sub(r"<script[^>]*>.*?</script>", "", c, flags=re.DOTALL)
            c = sanitise_html(c.strip())
            return _restore_svg(c, svgs)

        content_h_px = page_h_px - 2 * top_mg_px
        break_h_px = (page_h_px - top_mg_px - mg_px) if compact else content_h_px
        if show_title:
            _title_h = int((bsz + 6) * lh + 22)  # h1
            _sub_h   = int((bsz - 2) * lh + min_gap + 2) if "::" in deck_name else 0
            title_h_est = _title_h + _sub_h
        else:
            title_h_est = 0
        accumulated_h = [title_h_est]

        def emit_page_break(use_margin=True):
            accumulated_h[0] = 0
            if mode == "preview":
                return (
                    '</div></div>'
                    '<div class="page-break-marker">'
                    '<span>' + _t("page_break_lbl") + '</span></div>'
                    '<div class="page"><div class="page-content">'
                )
            h = int(top_mg_px) if use_margin else 0
            return '<div style="break-before:page;height:{}px;display:block;margin:0;padding:0"></div>'.format(h)

        def _text_len(html_str):
            return len(re.sub(r'<[^>]+>', '', html_str or ''))

        def estimate_card_h(sections_count, has_image, text_chars=0, n_images=1):
            overhead = (18 if show_nums else 0) + sections_count * padh * 2 + max(0, sections_count - 1)
            cpp = max(15, int(65 * 13.0 / max(bsz, 8)))
            if text_chars > 0:
                n_lines = max(sections_count * 2, (text_chars + cpp - 1) // cpp)
            else:
                n_lines = sections_count * 3
            text_h = n_lines * bsz * lh
            img_est = min(n_images, 5) * img_h if has_image else 0
            base = overhead + text_h + img_est + min_gap + 10
            if compact:
                return int(base)
            return int(base * 1.1) if has_image else int(base * 1.05)

        cards_ok = 0
        cards_skip = 0
        card_items = []  # compact: [(orig_idx, est, parts)]

        if render_mode == 1:
            for idx, cid in enumerate(card_ids):
                try:
                    card = mw.col.get_card(cid)
                    note = card.note()
                    nt_name = note.note_type()["name"]
                    q = proc_media(clean_rendered(card.question()))
                    a = proc_media(clean_rendered(card.answer()))
                    if "image occlusion" in nt_name.lower():
                        if q:
                            q = '<div class="io-wrap">{}</div>'.format(q)
                        if a:
                            a = '<div class="io-wrap">{}</div>'.format(a)
                    if not q and not a:
                        cards_skip += 1
                        continue

                    sec_count = (1 if q else 0) + (1 if a else 0)
                    has_img = "base64" in (q or '') or "base64" in (a or '')
                    n_imgs = max(1, (q or '').count('base64') + (a or '').count('base64')) if has_img else 0
                    est = estimate_card_h(sec_count, has_img, _text_len((q or '') + (a or '')), n_imgs)

                    alt = ' style="background:{}"'.format(t["alt"]) if zebra and idx % 2 == 1 else ""
                    parts = ['<div class="card"{}>'.format(alt)]
                    if show_nums:
                        parts.append('<div class="cnum">#{} &middot; {}</div>'.format(idx + 1, nt_name))
                    if q:
                        parts.append(
                            '<div class="sec-q"><div class="rs">'
                            '<div class="label">{}</div>{}</div></div>'.format(_t("rendered_front"), q))
                    if q and a:
                        parts.append('<hr class="sec-div">')
                    if a:
                        parts.append(
                            '<div class="sec-a"><div class="rs">'
                            '<div class="label">{}</div>{}</div></div>'.format(
                                _t("rendered_back"), a))
                    parts.append("</div>")

                    if compact:
                        card_items.append((idx, est, parts))
                    else:
                        accumulated_h[0] += est
                        if accumulated_h[0] > content_h_px:
                            pb = emit_page_break(est <= page_h_px * 0.75)
                            if pb:
                                html.append(pb)
                            accumulated_h[0] = est
                        html.extend(parts)
                    cards_ok += 1
                except Exception as e:
                    logger.error("Karta #{}".format(idx), e)
                    cards_skip += 1
        else:
            for idx, cid in enumerate(card_ids):
                try:
                    card = mw.col.get_card(cid)
                    note = card.note()
                    nt = note.note_type()
                    fmap = {}
                    for fm in nt["flds"]:
                        fmap[fm["name"]] = proc_raw(note.fields[fm["ord"]].strip())
                    sq, sa, sx = [], [], []
                    for w in self.field_widgets:
                        fn = w.field_name
                        if fn not in fc or not fc[fn]["export"]:
                            continue
                        val = fmap.get(fn, "")
                        if not val:
                            continue
                        r = render_field(fn, val, fc[fn])
                        s = fc[fn]["section"]
                        if s == 0:
                            sq.append(r)
                        elif s == 1:
                            sa.append(r)
                        else:
                            sx.append(r)
                    if not sq and not sa and not sx:
                        cards_skip += 1
                        continue

                    sec_count = (1 if sq else 0) + (1 if sa else 0) + (1 if sx else 0)
                    all_content = "".join(sq) + "".join(sa) + "".join(sx)
                    has_img = "base64" in all_content
                    n_imgs = max(1, all_content.count('base64')) if has_img else 0
                    est = estimate_card_h(sec_count, has_img, _text_len(all_content), n_imgs)

                    alt = ' style="background:{}"'.format(t["alt"]) if zebra and idx % 2 == 1 else ""
                    parts = ['<div class="card"{}>'.format(alt)]
                    if show_nums:
                        parts.append('<div class="cnum">#{}</div>'.format(idx + 1))
                    if sq:
                        parts.append('<div class="sec-q">{}</div>'.format("".join(sq)))
                    if sq and sa:
                        parts.append('<hr class="sec-div">')
                    if sa:
                        parts.append('<div class="sec-a">{}</div>'.format("".join(sa)))
                    if sx and (sq or sa):
                        parts.append('<hr class="sec-div">')
                    if sx:
                        parts.append('<div class="sec-x">{}</div>'.format("".join(sx)))
                    parts.append("</div>")

                    if compact:
                        card_items.append((idx, est, parts))
                    else:
                        accumulated_h[0] += est
                        if accumulated_h[0] > content_h_px:
                            pb = emit_page_break(est <= page_h_px * 0.75)
                            if pb:
                                html.append(pb)
                            accumulated_h[0] = est
                        html.extend(parts)
                    cards_ok += 1
                except Exception as e:
                    logger.error("Karta #{}".format(idx), e)
                    cards_skip += 1

        if compact and card_items:
            if mode == "pdf":
                # Sequential bin-packing: explicit break-before:page divs with
                # height:0 — @page margin-top handles top spacing, no spacer needed.
                # Break only when adding the next card would overflow, and only if
                # at least one card is already on the current page (prevents empty pages).
                acc_h = title_h_est
                cards_on_page = 0
                for _, est, parts in card_items:
                    if acc_h + est > break_h_px and cards_on_page > 0:
                        html.append(
                            '<div style="break-before:page;height:0;'
                            'display:block;margin:0;padding:0"></div>'
                        )
                        acc_h = 0
                        cards_on_page = 0
                    acc_h += est
                    cards_on_page += 1
                    html.extend(parts)
            else:
                # Preview: Python FFD with estimates + explicit page-break markers
                sorted_items = sorted(card_items, key=lambda c: c[1], reverse=True)
                pages_ffd = []
                pages_used = []
                for item in sorted_items:
                    _, est, parts = item
                    placed = False
                    for pi in range(len(pages_ffd)):
                        if pages_used[pi] + est <= break_h_px:
                            pages_ffd[pi].append(item)
                            pages_used[pi] += est
                            placed = True
                            break
                    if not placed:
                        pages_ffd.append([item])
                        pages_used.append(est)
                pages_ffd.sort(key=lambda p: min(c[0] for c in p))
                for page in pages_ffd:
                    page.sort(key=lambda c: c[0])
                for pi, page_cards in enumerate(pages_ffd):
                    if pi > 0:
                        pb = emit_page_break()
                        if pb:
                            html.append(pb)
                    for *_, parts in page_cards:
                        html.extend(parts)

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
                "function openImg(src){"
                "sc=1;ox=0;oy=0;"
                "li.classList.add('no-anim');"
                "li.style.transform='';"
                "li.onload=function(){fitToView();};"
                "li.src=src;"
                "lbx.classList.add('open');"
                "document.body.style.overflow='hidden';"
                "if(li.complete&&li.naturalWidth)fitToView();"
                "}"
                "function closeViewer(){"
                "lbx.classList.remove('open');"
                "li.src='';"
                "document.body.style.overflow='';"
                "}"
                "if(pc)pc.addEventListener('click',function(e){"
                "var t=e.target;"
                "while(t&&t!==pc){"
                "if(t.tagName==='IMG'){openImg(t.src);return;}"
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
                "li.addEventListener('dblclick',function(e){"
                "e.stopPropagation();"
                "if(Math.abs(sc-fitScale)<0.01){"
                "var rect=lbx.getBoundingClientRect();"
                "var mx=e.clientX-rect.width/2-ox;"
                "var my=e.clientY-rect.height/2-oy;"
                "var ds=1/sc;"
                "ox-=mx*(ds-1);oy-=my*(ds-1);sc=1;"
                "}else{sc=fitScale;ox=0;oy=0;}"
                "li.classList.remove('no-anim');applyT();"
                "});"
                "})();</script>"
            )

        html.append("</body></html>")
        result = "".join(html)
        logger.log("OK: {}, skip: {}".format(cards_ok, cards_skip))
        logger.log("Img OK: {}, fail: {}".format(img_ok[0], img_fail[0]))
        return result, card_ids


_dlg = None


def show_export_dialog():
    global _dlg
    _dlg = PDFExportDialog(mw)
    _dlg.show()
    _dlg.raise_()
    _dlg.activateWindow()


action = QAction(_t("menu_action"), mw)
action.triggered.connect(show_export_dialog)
mw.form.menuTools.addAction(action)


def _quick_legacy_export():
    """Open the currently focused deck as Legacy HTML (Shift+P shortcut)."""
    if not mw.col:
        return
    global _dlg
    if _dlg is None:
        _dlg = PDFExportDialog(mw)
    cur = mw.col.decks.current()
    if cur:
        top = cur["name"].split("::")[0]
        idx = _dlg.deck_combo.findText(top)
        if idx >= 0:
            _dlg.deck_combo.setCurrentIndex(idx)
        if "::" in cur["name"]:
            sidx = _dlg.subdeck_combo.findData(cur["name"])
            if sidx >= 0:
                _dlg.subdeck_combo.setCurrentIndex(sidx)
    _dlg._on_legacy()


_legacy_shortcut = QShortcut(QKeySequence("Shift+P"), mw)
_legacy_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
_legacy_shortcut.activated.connect(_quick_legacy_export)
