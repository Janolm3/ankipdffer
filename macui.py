"""macOS-style (Yosemite – Catalina era) look for the export window.

Everything visual lives here: the colour palette, the Qt stylesheet, a few small
SVG glyphs the stylesheet points at, and two widgets Qt does not provide —
a segmented control and a tab box with the segmented control centred on its top edge.
"""
import hashlib
import os
import re
import tempfile

from aqt.qt import (
    QButtonGroup, QColor, QEvent, QFrame, QHBoxLayout, QIcon, QLabel, QObject, QPainter,
    QPen, QPixmap, QPushButton, QRectF, QScrollArea, QSize, QSizePolicy, QStackedWidget,
    QStyledItemDelegate, QVBoxLayout, QWidget, Qt,
)

LIGHT = dict(
    window="#ececec", toolbar="#e3e3e3", hairline="#c9c9c9", footer_line="#d4d4d4",
    box="rgba(0,0,0,0.035)", box_border="#d6d6d8",
    control="#ffffff", control_border="#c9c9cc",
    control_pressed="#e6e6e6", field="#ffffff", field_border="#c4c4c7",
    text="#1d1d1f", secondary="#86868b", disabled="#a8a8ad", control_disabled="#f6f6f6",
    accent="#007aff", accent_pressed="#0062cc", accent_soft="rgba(0,122,255,0.14)",
    destructive="#ff3b30",
    danger="#bf5a54", danger_pressed="#a94c47", danger_border="#a54843", danger_text="#ffffff",
    track="rgba(118,118,128,0.14)", tab_track="#dbdbdd", thumb="#ffffff", thumb_border="#d2d2d5",
    table="#ffffff", table_line="#e5e5e5", hover="rgba(0,0,0,0.05)",
    scroll="rgba(0,0,0,0.28)", menu="#f6f6f6",
    hud="rgba(30,30,32,0.90)", veil="rgba(236,236,236,0.55)",
    glyph="#6e6e73",
)

DARK = dict(
    window="#2b2b2d", toolbar="#353537", hairline="#1a1a1a", footer_line="#3d3d40",
    box="rgba(255,255,255,0.035)", box_border="#3f3f42",
    control="#5b5b5f", control_border="#68686c",
    control_pressed="#6d6d72", field="#1f1f21", field_border="#424245",
    text="#ececee", secondary="#98989d", disabled="#88888d", control_disabled="#434346",
    accent="#0a84ff", accent_pressed="#0070e0", accent_soft="rgba(10,132,255,0.22)",
    destructive="#ff453a",
    danger="#97443f", danger_pressed="#863a36", danger_border="#7a3430", danger_text="#f7ecea",
    track="rgba(118,118,128,0.26)", tab_track="#3e3e43", thumb="#68686d", thumb_border="#747479",
    table="#323235", table_line="#3f3f43", hover="rgba(255,255,255,0.06)",
    scroll="rgba(255,255,255,0.30)", menu="#2f2f31",
    hud="rgba(30,30,32,0.92)", veil="rgba(20,20,22,0.45)",
    glyph="#a1a1a6",
)


_current = LIGHT


def palette(dark):
    return DARK if dark else LIGHT


def current():
    """Palette of the last stylesheet built (what the custom-painted widgets use)."""
    return _current


def qcolor(value):
    """CSS colour (hex or rgba()) -> QColor."""
    m = _RGBA_RE.match(value.strip())
    if m:
        r, g, b, a = m.groups()
        return QColor(int(r), int(g), int(b), int(round(float(a) * 255)))
    return QColor(value)


# ------------------------------------------------------------------ glyphs
_GLYPHS = {
    # Small rounded shapes are drawn as SVG: Qt clips stylesheet backgrounds with rounded
    # corners without antialiasing, which looks jagged; SVG paths are antialiased.
    "popup": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
             '<rect x="0" y="0" width="16" height="16" rx="4" {accent_fill}/>'
             '<path d="M5.2 6.4 8 3.6l2.8 2.8M5.2 9.6 8 12.4l2.8-2.8" fill="none" stroke="#ffffff" '
             'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "popup_off": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
                 '<rect x="0" y="0" width="16" height="16" rx="4" {disabled_fill}/>'
                 '<path d="M5.2 6.4 8 3.6l2.8 2.8M5.2 9.6 8 12.4l2.8-2.8" fill="none" stroke="#ffffff" '
                 'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "box": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14">'
           '<rect x="0.5" y="0.5" width="13" height="13" rx="3.5" {field_fill} {field_border_stroke} '
           'stroke-width="1"/></svg>',
    "box_on": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14">'
              '<rect x="0" y="0" width="14" height="14" rx="4" {accent_fill}/>'
              '<path d="M3.6 7.3 6 9.6l4.4-5.2" fill="none" stroke="#ffffff" stroke-width="1.8" '
              'stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "box_on_off": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14">'
                  '<rect x="0" y="0" width="14" height="14" rx="4" {disabled_fill}/>'
                  '<path d="M3.6 7.3 6 9.6l4.4-5.2" fill="none" stroke="#ffffff" stroke-width="1.8" '
                  'stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "box_off": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14">'
               '<rect x="0.5" y="0.5" width="13" height="13" rx="3.5" {control_disabled_fill} '
               '{field_border_stroke} stroke-width="1"/></svg>',
    "up": '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="5" viewBox="0 0 8 5">'
          '<path d="M1 4 4 1l3 3" fill="none" {glyph_stroke} stroke-width="1.4" '
          'stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "down": '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="5" viewBox="0 0 8 5">'
            '<path d="M1 1l3 3 3-3" fill="none" {glyph_stroke} stroke-width="1.4" '
            'stroke-linecap="round" stroke-linejoin="round"/></svg>',
    # line.3.horizontal.decrease (filter); the "on" variant is drawn in the accent colour
    "filter": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14">'
              '<path d="M2 3.5h10M4 7h6M5.8 10.5h2.4" fill="none" {glyph_stroke} stroke-width="1.5" '
              'stroke-linecap="round"/></svg>',
    "filter_on": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14">'
                 '<circle cx="7" cy="7" r="7" {accent_fill}/>'
                 '<path d="M3.6 4.6h6.8M5 7h4M6.1 9.4h1.8" fill="none" stroke="#ffffff" '
                 'stroke-width="1.4" stroke-linecap="round"/></svg>',
    "minus_circle": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
                    '<circle cx="8" cy="8" r="7.25" fill="none" {glyph_stroke} stroke-width="1.2"/>'
                    '<path d="M5 8h6" {glyph_stroke} stroke-width="1.5" stroke-linecap="round"/></svg>',
    "plus_circle": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
                   '<circle cx="8" cy="8" r="7.25" fill="none" {glyph_stroke} stroke-width="1.2"/>'
                   '<path d="M5 8h6M8 5v6" {glyph_stroke} stroke-width="1.5" stroke-linecap="round"/></svg>',
    "search": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14">'
              '<circle cx="6" cy="6" r="4.2" fill="none" {glyph_stroke} stroke-width="1.5"/>'
              '<path d="m9.2 9.2 3.3 3.3" {glyph_stroke} stroke-width="1.6" stroke-linecap="round"/></svg>',
}

_RGBA_RE = re.compile(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)")


def _svg_paint(value, attr):
    """CSS colour -> SVG attributes (Qt's SVG renderer wants hex + separate opacity)."""
    m = _RGBA_RE.match(value.strip())
    if m:
        r, g, b, a = m.groups()
        return '{0}="#{1:02x}{2:02x}{3:02x}" {0}-opacity="{4}"'.format(attr, int(r), int(g), int(b), a)
    return '{}="{}"'.format(attr, value)


def _glyph_dir():
    path = os.path.join(tempfile.gettempdir(), "ankipdffer-ui")
    os.makedirs(path, exist_ok=True)
    return path


def glyph_path(name, pal):
    """Write the glyph (coloured for `pal`) once and return a stylesheet-safe path."""
    paints = {}
    for key in ("accent", "disabled", "field", "control_disabled", "field_border", "glyph"):
        paints[key + "_fill"] = _svg_paint(pal[key], "fill")
        paints[key + "_stroke"] = _svg_paint(pal[key], "stroke")
    svg = _GLYPHS[name]
    for key, val in paints.items():
        svg = svg.replace("{" + key + "}", val)
    digest = hashlib.sha1(svg.encode("utf-8")).hexdigest()[:10]
    path = os.path.join(_glyph_dir(), "{}-{}.svg".format(name, digest))
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
    return path.replace("\\", "/")


def dot_icon(color, size=12):
    """Round colour swatch for pop-up menus (SVG, so it stays sharp)."""
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 12 12">'
           '<circle cx="6" cy="6" r="5" {fill} stroke="#000000" stroke-opacity="0.18" '
           'stroke-width="1"/></svg>').format(s=size, fill=_svg_paint(color, "fill"))
    digest = hashlib.sha1(svg.encode("utf-8")).hexdigest()[:10]
    path = os.path.join(_glyph_dir(), "dot-{}.svg".format(digest))
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
    return QIcon(path)


def glyph_icon(name, pal, size=14):
    """Vector icon: Qt's SVG icon engine renders it sharp at any size and pixel ratio."""
    icon = QIcon(glyph_path(name, pal))
    if icon.isNull():
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        icon = QIcon(pix)
    return icon


_EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]+\\s*")


def plain(text):
    """Strip the decorative emoji older string tables carry ("☀️ Light" -> "Light")."""
    return _EMOJI_RE.sub("", text or "").strip()


# -------------------------------------------------------------- stylesheet
def stylesheet(dark):
    global _current
    _current = palette(dark)
    p = dict(_current)
    p.update({name: glyph_path(name, p) for name in
              ("popup", "popup_off", "box", "box_on", "box_on_off", "box_off", "up", "down")})
    return _QSS.format(**p)


_QSS = """
QDialog#PdfferWindow {{ background: {window}; }}
QWidget {{ color: {text}; font-size: 13px; }}
QLabel, QCheckBox {{ background: transparent; }}
QToolTip {{ color: {text}; background: {menu}; border: 1px solid {box_border}; padding: 4px 6px; }}

/* ---------- window chrome ---------- */
QFrame#Toolbar {{ background: {toolbar}; border: none; border-bottom: 1px solid {hairline}; }}
QFrame#Footer {{ background: {window}; border: none; border-top: 1px solid {footer_line}; }}
QFrame#TabFrame, QFrame#Table, QFrame#BusyPanel, QFrame#Segmented {{ background: transparent; border: none; }}
QWidget#Page, QScrollArea#PageScroll, QScrollArea#PageScroll > QWidget > QWidget {{ background: transparent; }}
QScrollArea {{ border: none; background: transparent; }}
QFrame#Separator {{ background: {box_border}; border: none; max-height: 1px; min-height: 1px; }}

QLabel#Secondary, QLabel#HintLabel, QLabel#CountLabel, QLabel#VersionLabel,
QLabel#SettingsInfoLabel, QLabel#BusyLabel {{ color: {secondary}; font-size: 12px; }}
QLabel#HintLabel {{ font-size: 11px; }}
QLabel#CountLabel[error="true"] {{ color: {destructive}; }}
QLabel#FormLabel {{ color: {text}; }}
QLabel:disabled {{ color: {disabled}; }}
QLabel#ColumnHeader {{ color: {secondary}; font-size: 10px; font-weight: 600; }}
QWidget#TableColumns {{ background: transparent; border-bottom: 1px solid {table_line}; }}
QLabel#ToolbarLabel {{ color: {secondary}; font-size: 12px; }}
QLabel#Chevron {{ color: {secondary}; font-size: 15px; }}

/* ---------- push buttons ---------- */
QPushButton {{
    background: {control}; color: {text}; background-clip: padding;
    border: 1px solid {control_border};
    border-radius: 6px; padding: 3px 14px; min-height: 18px; font-size: 13px;
}}
QPushButton:pressed {{ background: {control_pressed}; }}
QPushButton:disabled {{ color: {disabled}; background: {control_disabled}; }}
QPushButton#Primary {{
    background: {accent}; color: #ffffff; border: 1px solid {accent_pressed};
}}
QPushButton#Primary:pressed {{ background: {accent_pressed}; }}
QPushButton#Primary:disabled {{ background: {accent_soft}; color: rgba(255,255,255,0.7); border-color: transparent; }}
QPushButton#Destructive:hover {{
    background: {danger}; color: {danger_text}; border: 1px solid {danger_border};
}}
QPushButton#Destructive:pressed {{
    background: {danger_pressed}; color: {danger_text}; border: 1px solid {danger_border};
}}
QPushButton#Plain {{
    background: transparent; border: 1px solid transparent; color: {secondary};
    padding: 0; min-height: 22px; min-width: 22px; border-radius: 6px; font-size: 15px;
}}
QPushButton#Plain:hover {{ background: {hover}; color: {text}; }}
QPushButton#Plain:checked {{ background: {accent_soft}; color: {accent}; }}

/* ---------- segmented control ---------- */
QPushButton#Segment, QPushButton#Segment:checked, QPushButton#Segment:hover, QPushButton#Segment:pressed {{
    background: transparent; border: none;
    padding: 3px 12px; min-height: 16px; font-size: 12px; color: {text};
}}
QPushButton#Segment:disabled {{ color: {disabled}; }}

/* ---------- pop-up buttons ---------- */
QComboBox {{
    background: {control}; color: {text}; background-clip: padding;
    border: 1px solid {control_border};
    border-radius: 5px; padding: 2px 28px 2px 8px; min-height: 18px; font-size: 13px;
    combobox-popup: 0;
}}
QComboBox:disabled {{ color: {disabled}; background: {control_disabled}; }}
QComboBox::drop-down {{
    subcontrol-origin: padding; subcontrol-position: center right;
    width: 16px; right: 3px; border: none; background: transparent;
}}
QComboBox::down-arrow {{ image: url("{popup}"); width: 16px; height: 16px; }}
QComboBox::down-arrow:disabled {{ image: url("{popup_off}"); }}
QComboBoxPrivateContainer {{ background: transparent; border: none; }}
QComboBox QAbstractItemView {{
    background: {menu}; color: {text}; border: 1px solid {box_border}; border-radius: 6px;
    padding: 4px; outline: 0; background-clip: padding;
    selection-background-color: {accent}; selection-color: #ffffff;
}}
QComboBox QAbstractItemView::item {{ min-height: 22px; padding: 0 10px; border: none; border-radius: 4px; color: {text}; }}
QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover {{ background: {accent}; color: #ffffff; }}
QComboBox QAbstractItemView::item:disabled {{ color: {disabled}; background: transparent; }}

/* ---------- menus ---------- */
QMenu {{ background: {menu}; color: {text}; border: 1px solid {box_border}; border-radius: 6px; padding: 4px; background-clip: padding; }}
QMenu::item {{ padding: 3px 20px 3px 14px; border-radius: 4px; }}
QMenu::item:selected {{ background: {accent}; color: #ffffff; }}
QMenu::item:disabled {{ color: {disabled}; background: transparent; }}
QMenu::separator {{ height: 1px; background: {box_border}; margin: 4px 6px; }}
QPushButton::menu-indicator {{ image: url("{down}"); subcontrol-origin: padding; subcontrol-position: right center; right: 8px; width: 8px; height: 5px; }}
QPushButton[menuButton="true"] {{ padding-right: 24px; }}

/* ---------- text fields / steppers ---------- */
QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
    background: {field}; color: {text}; background-clip: padding;
    border: 1px solid {field_border}; border-radius: 5px;
    padding: 2px 6px; min-height: 18px; font-size: 13px;
    selection-background-color: {accent}; selection-color: #ffffff;
}}
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border: 1px solid {accent}; }}
QLineEdit#SearchField {{ border-radius: 7px; padding: 3px 6px; }}
QSpinBox, QDoubleSpinBox {{ padding-right: 18px; }}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border; subcontrol-position: top right;
    width: 16px; border: none; background: transparent; margin: 2px 2px 0 0;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border; subcontrol-position: bottom right;
    width: 16px; border: none; background: transparent; margin: 0 2px 2px 0;
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url("{up}"); width: 8px; height: 5px; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url("{down}"); width: 8px; height: 5px; }}

/* ---------- check boxes ---------- */
QCheckBox {{ spacing: 6px; min-height: 20px; }}
QCheckBox:disabled {{ color: {disabled}; }}
QCheckBox::indicator {{ width: 14px; height: 14px; border: none; background: transparent; image: url("{box}"); }}
QCheckBox::indicator:checked {{ image: url("{box_on}"); }}
QCheckBox::indicator:disabled {{ image: url("{box_off}"); }}
QCheckBox::indicator:checked:disabled {{ image: url("{box_on_off}"); }}

/* ---------- Fields tab table ---------- */
QLabel#TableHeader {{ color: {secondary}; font-size: 11px; font-weight: 600; letter-spacing: 0.4px; }}
FieldConfigWidget {{ background: transparent; }}
FieldConfigWidget[last="false"] {{ border-bottom: 1px solid {table_line}; }}
QWidget#FilterRow {{ background: transparent; }}
QWidget#FilterRow[last="false"] {{ border-bottom: 1px solid {table_line}; }}
QLabel#QueryLabel {{ color: {secondary}; font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 11px; }}

/* ---------- progress ---------- */
QProgressBar {{ background: {track}; border: none; border-radius: 2px; max-height: 4px; min-height: 4px; }}
QProgressBar::chunk {{ background: {accent}; border-radius: 2px; }}
QFrame#BusyOverlay {{ background: {veil}; border: none; }}
QLabel#BusyOverlayLabel {{ color: #ffffff; font-size: 13px; font-weight: 600; }}
QLabel#BusyOverlayHint {{ color: rgba(255,255,255,0.62); font-size: 11px; }}
QFrame#BusyPanel QProgressBar {{ background: rgba(255,255,255,0.18); }}
QFrame#BusyPanel QProgressBar::chunk {{ background: #ffffff; }}

/* ---------- scroll bars (overlay style) ---------- */
QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {scroll}; min-height: 28px; border-radius: 2px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; border: none; background: none; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
QScrollBar:horizontal {{ height: 0; }}
"""


# ----------------------------------------------------------------- widgets
def _antialiased(widget):
    painter = QPainter(widget)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    return painter


def _rounded(painter, rect, radius, fill, stroke=None):
    """Antialiased rounded rectangle; a 1px stroke sits on the half-pixel grid to stay crisp."""
    r = QRectF(rect)
    if stroke:
        r = r.adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QPen(qcolor(stroke), 1))
    else:
        painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(qcolor(fill))
    painter.drawRoundedRect(r, radius, radius)


class RoundedFrame(QFrame):
    """Container with an antialiased rounded background (stylesheets clip corners jaggedly)."""

    def __init__(self, fill_key, stroke_key=None, radius=8, parent=None):
        super().__init__(parent)
        self._fill_key, self._stroke_key, self._radius = fill_key, stroke_key, radius

    def paintEvent(self, event):
        pal = current()
        p = _antialiased(self)
        _rounded(p, self.rect(), self._radius, pal[self._fill_key],
                 pal[self._stroke_key] if self._stroke_key else None)
        p.end()
        super().paintEvent(event)


class SegmentedControl(QFrame):
    """NSSegmentedControl look-alike.

    Exposes the same small API the dialog used for its radio groups: `currentIndex()`,
    `setCurrentIndex()`, `.buttons` and `.group` (a QButtonGroup, so `idToggled` works).
    With `exclusive=False` it is a strip of independent toggles (B / I / U).
    """

    def __init__(self, options, default=0, exclusive=True, parent=None):
        super().__init__(parent)
        self.setObjectName("Segmented")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        ly = QHBoxLayout(self)
        ly.setContentsMargins(2, 2, 2, 2)
        ly.setSpacing(1)
        self.group = QButtonGroup(self)
        self.group.setExclusive(exclusive)
        self.buttons = []
        self._current_index = default if 0 <= default < len(options) else 0
        for i, label in enumerate(options):
            btn = QPushButton(plain(label))
            btn.setObjectName("Segment")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            if exclusive and i == self._current_index:
                btn.setChecked(True)
            btn.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
            btn.installEventFilter(self)
            self.group.addButton(btn, i)
            self.buttons.append(btn)
            ly.addWidget(btn)
        self.group.idToggled.connect(self._on_toggled)
        self.group.idToggled.connect(lambda *_: self.update())

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.Enter, QEvent.Type.Leave, QEvent.Type.EnabledChange):
            self.update()
        return False

    def paintEvent(self, event):
        """Track, then a raised thumb under every checked segment (antialiased)."""
        pal = current()
        p = _antialiased(self)
        if not self.isEnabled():
            p.setOpacity(0.55)
        tabs = self.property("role") == "tabs"
        _rounded(p, self.rect(), 7, pal["tab_track"] if tabs else pal["track"])
        for btn in self.buttons:
            if not btn.isVisible():
                continue
            geo = btn.geometry()
            if btn.isChecked():
                _rounded(p, geo, 5, pal["thumb"], pal["thumb_border"])
            elif btn.underMouse() and btn.isEnabled():
                _rounded(p, geo, 5, pal["hover"])
        p.end()

    def _on_toggled(self, idx, checked):
        if checked:
            self._current_index = idx

    def currentIndex(self):
        return self._current_index

    def setCurrentIndex(self, idx):
        if 0 <= idx < len(self.buttons):
            self._current_index = idx
            self.buttons[idx].setChecked(True)

    def setSegmentVisible(self, idx, visible):
        self.buttons[idx].setVisible(visible)


class TabBox(QWidget):
    """NSTabView look: an inset box with its segmented tab selector centred on the top edge."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame = RoundedFrame("box", "box_border", 8, self)
        self.frame.setObjectName("TabFrame")
        self.stack = QStackedWidget(self.frame)
        self._frame_ly = QVBoxLayout(self.frame)
        self._frame_ly.setContentsMargins(1, 0, 1, 1)
        self._frame_ly.addWidget(self.stack)
        self.tabs = None
        self._labels = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def add_page(self, label, widget):
        self._labels.append(label)
        self.stack.addWidget(widget)

    def finish(self):
        """Build the selector once all pages are added."""
        self.tabs = SegmentedControl(self._labels, default=0, parent=self)
        self.tabs.setProperty("role", "tabs")
        self.tabs.group.idToggled.connect(
            lambda idx, checked: checked and self.stack.setCurrentIndex(idx))
        self.tabs.raise_()
        self._relayout()

    def _half(self):
        return (self.tabs.sizeHint().height() // 2) if self.tabs else 0

    def _relayout(self):
        if not self.tabs:
            return
        self.tabs.layout().activate()
        half = self._half()
        self._frame_ly.setContentsMargins(1, half + 10, 1, 1)
        hint = self.tabs.sizeHint()
        self.tabs.setGeometry((self.width() - hint.width()) // 2, 0, hint.width(), hint.height())
        self.frame.setGeometry(0, half, self.width(), max(0, self.height() - half))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout()

    def setSegmentVisible(self, idx, visible):
        self.tabs.setSegmentVisible(idx, visible)
        self._relayout()

    def minimumSizeHint(self):
        inner = self.frame.minimumSizeHint()
        return QSize(max(inner.width(), self.tabs.sizeHint().width() if self.tabs else 0),
                     inner.height() + self._half())

    def sizeHint(self):
        inner = self.frame.sizeHint()
        return QSize(inner.width(), inner.height() + self._half())


def separator():
    line = QFrame()
    line.setObjectName("Separator")
    line.setFrameShape(QFrame.Shape.NoFrame)
    return line


def form_label(text):
    lbl = QLabel(text)
    lbl.setObjectName("FormLabel")
    return lbl


class ElidedLabel(QLabel):
    """Plain-text label that shrinks with an ellipsis instead of forcing its width."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._full = text
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setToolTip(text)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        super().setText(text)

    def setText(self, text):
        self._full = text or ""
        self.updateGeometry()
        super().setText(self.fontMetrics().elidedText(
            self._full, Qt.TextElideMode.ElideRight, max(self.width(), 1)) if self.width() > 1 else self._full)

    def text(self):
        return self._full

    def sizeHint(self):
        hint = super().sizeHint()
        return QSize(self.fontMetrics().horizontalAdvance(self._full) + 4, hint.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        elided = self.fontMetrics().elidedText(self._full, Qt.TextElideMode.ElideRight, self.width())
        if elided != super().text():
            super().setText(elided)


class FitWidthScrollArea(QScrollArea):
    """Vertical-only scroll area whose minimum width is its content's, so forms never clip."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def minimumSizeHint(self):
        inner = self.widget()
        width = inner.minimumSizeHint().width() if inner else 0
        return QSize(width + self.verticalScrollBar().sizeHint().width(), 160)


class PopupItemDelegate(QStyledItemDelegate):
    """Mac-style pop-up rows (stylesheet-driven) with real separator lines."""

    def __init__(self, line_color, parent=None):
        super().__init__(parent)
        self._line = QColor(line_color)

    @staticmethod
    def _is_separator(index):
        return index.data(Qt.ItemDataRole.AccessibleDescriptionRole) == "separator"

    def paint(self, painter, option, index):
        if self._is_separator(index):
            painter.save()
            painter.setPen(QPen(self._line, 1))
            y = option.rect.center().y()
            painter.drawLine(option.rect.left() + 8, y, option.rect.right() - 8, y)
            painter.restore()
            return
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        if self._is_separator(index):
            return QSize(0, 9)
        return super().sizeHint(option, index)


class _PopupFrameFix(QObject):
    """Qt re-applies the combo popup container's square frame when it is shown."""

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.Show, QEvent.Type.Polish):
            obj.setFrameShape(QFrame.Shape.NoFrame)
            obj.setLineWidth(0)
        return False


def round_popup(widget, pal=None):
    """Let a menu / combo-box list window show its rounded corners (no square backing)."""
    if hasattr(widget, "view"):
        widget.setItemDelegate(PopupItemDelegate((pal or LIGHT)["box_border"], widget))
    win = widget.view().window() if hasattr(widget, "view") else widget
    if hasattr(widget, "view"):
        container = widget.view().parentWidget()
        if isinstance(container, QFrame):
            fix = _PopupFrameFix(container)
            container.installEventFilter(fix)
            container.setFrameShape(QFrame.Shape.NoFrame)
            container.setLineWidth(0)
    win.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
    win.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, False)
    win.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
