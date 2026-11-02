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
    QButtonGroup, QColor, QEvent, QFont, QFontMetricsF, QFrame, QHBoxLayout, QIcon, QLabel, QObject,
    QPainter, QPainterPath, QPainterPathStroker, QPen, QPixmap, QPointF, QPushButton, QRectF, QScrollArea, QSize,
    QSizePolicy, QStackedWidget, QStyledItemDelegate, QVBoxLayout, QWidget, Qt, pyqtSignal,
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
/* the tab selector is a little roomier than the other segmented controls */
QFrame#Segmented[role="tabs"] QPushButton#Segment, QFrame#Segmented[role="tabs"] QPushButton#Segment:checked,
QFrame#Segmented[role="tabs"] QPushButton#Segment:hover, QFrame#Segmented[role="tabs"] QPushButton#Segment:pressed {{
    padding: 3px 17px;
}}

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
QSpinBox[linked="true"], QDoubleSpinBox[linked="true"], QComboBox[linked="true"] {{ border: 1px solid {accent}; }}
QCheckBox[linked="true"] {{ color: {accent}; }}
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


class PagePreview(QWidget):
    """A sketch of an exported page, drawn to scale from the Page and Appearance options.

    The sheet has the chosen paper size; margins are in millimetres and padding, gaps and the
    image limit in CSS pixels (0.2646 mm), exactly as the export CSS reads them, so changing an
    option moves the sketch the way it will move the PDF. Dimension lines mark what each option
    measures and lead to labelled values beside the sheet (`notes`: key -> text).

    The option being edited (`set_focus`) is drawn strongly - tinted area, accent dimension line,
    filled label - and the others step back; the one under the pointer, in the form or here
    (`set_hover`, `hovered`), is marked lightly. Clicking a mark or label emits `picked`.
    Keys: margin, top, padding, gap, lh, img, numbers, info, page.
    """

    picked = pyqtSignal(str)
    hovered = pyqtSignal(object)  # key under the pointer, or None

    PX_MM = 25.4 / 96
    CARDS = ((2, 3, False), (1, 2, True), (2, 4, False), (1, 3, False), (2, 2, False), (1, 4, False))
    BARS = (0.94, 0.78, 0.88, 0.52, 0.84, 0.66, 0.9, 0.4)
    IMAGE_PX = (520, 4 / 3)  # natural height of the sample picture and its aspect ratio
    NOTE_PX = 11  # label font size
    LABEL_GAP = 5  # space between two labels
    PAD = 6  # space around the sheet
    SHEET_W = (150, 440)  # the sheet's width range; within it the height decides

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(250)
        self.setMinimumWidth(240)
        self.setMouseTracking(True)
        self._p = {}
        self._focus = None
        self._hover_out = None  # from the form
        self._hover_in = None  # from the pointer over the sketch
        self._hits = []
        self._labels = []
        self._sheet = QRectF()
        self._lanes = (0, [])
        self._want = 360

    def sizeHint(self):
        return QSize(self._want, 380)

    def set_params(self, **params):
        if params != self._p:
            self._p = params
            self._fit_width()
            self.update()

    def set_focus(self, key):
        if key != self._focus:
            self._focus = key
            self.update()

    def set_hover(self, key):
        if key != self._hover_out:
            self._hover_out = key
            self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_width()

    # ------------------------------------------------------------ pointer
    def _key_at(self, pos):
        for rect, key in self._hits:
            if rect.contains(QPointF(pos)):
                return key
        return None

    def mouseMoveEvent(self, event):
        key = self._key_at(event.position())
        if key != self._hover_in:
            self._hover_in = key
            self.setCursor(Qt.CursorShape.PointingHandCursor if key else Qt.CursorShape.ArrowCursor)
            self.hovered.emit(key)
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self._hover_in is not None:
            self._hover_in = None
            self.unsetCursor()
            self.hovered.emit(None)
            self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        key = self._key_at(event.position())
        if key and event.button() == Qt.MouseButton.LeftButton:
            self.picked.emit(key)
        super().mousePressEvent(event)

    # ------------------------------------------------------------ size
    def _note_font(self, bold=False):
        font = QFont(self.font())
        font.setPixelSize(self.NOTE_PX)
        font.setBold(bold)
        return font

    def _gutter(self):
        """Width of the label column right of the sheet."""
        notes = self._p.get("notes") or {}
        if not notes:
            return 0
        metrics = QFontMetricsF(self._note_font(True))
        return int(max(metrics.horizontalAdvance(text) for text in notes.values())) + 34

    def _fit_width(self):
        """Ask for the width the sheet drawn at this height needs, plus its labels, so the sketch
        sits flush in its column (it never insists: the minimum width stays small)."""
        if not self._p:
            return
        pw, ph = self._p["size"]
        sheet_w = max(self.SHEET_W[0], min(self.SHEET_W[1], (self.height() - 32) * pw / ph))
        want = int(sheet_w + 2 * self.PAD + self._gutter())
        if want != self._want:
            self._want = want
            self.setMaximumWidth(want)
            self.updateGeometry()

    # ------------------------------------------------------------ painting
    def _level(self, key):
        """2: the option being edited, 1: the one under the pointer, 0: neither."""
        if key == self._focus:
            return 2
        return 1 if key in (self._hover_in, self._hover_out) else 0

    def paintEvent(self, event):
        p = self._p
        if not p:
            return
        pal = current()
        t = p["tokens"]
        notes = p.get("notes") or {}
        gutter = self._gutter()
        pw, ph = p["size"]
        avail = QRectF(self.PAD, self.PAD, self.width() - 2 * self.PAD - gutter, self.height() - 32)
        if avail.width() < 20 or avail.height() < 20:
            return
        qp = _antialiased(self)
        scale = min(avail.width() / pw, avail.height() / ph, self.SHEET_W[1] / pw)  # px per mm
        sheet = QRectF(avail.left() + (avail.width() - pw * scale) / 2,
                       avail.center().y() - ph * scale / 2, pw * scale, ph * scale)
        px = scale * self.PX_MM  # screen px per CSS px
        accent = qcolor(pal["accent"])
        self._sheet = sheet

        qp.setPen(Qt.PenStyle.NoPen)
        for grow, alpha in ((3, 14), (1.5, 26)):  # soft shadow
            qp.setBrush(QColor(0, 0, 0, alpha))
            qp.drawRoundedRect(sheet.adjusted(-grow, -grow + 2, grow, grow + 2), 3 + grow, 3 + grow)
        _rounded(qp, sheet, 2, t["body"], "rgba(128,128,128,0.45)")

        margin, top = p["margin"], p["top"]
        info = p.get("info", True)
        bottom = max(top, 12) if p["numbers"] else max(top, 9) if info else top
        content = QRectF(sheet.left() + margin * scale, sheet.top() + top * scale,
                         sheet.width() - 2 * margin * scale,
                         sheet.height() - (top + bottom) * scale)
        guide = QColor(accent)
        guide.setAlpha(110)
        qp.setPen(QPen(guide, 0.8, Qt.PenStyle.DashLine))
        qp.setBrush(Qt.BrushStyle.NoBrush)
        qp.drawRect(content)

        bsz = p["font"]
        bar_h = max(1.5, bsz * 0.5 * px)
        pitch = max(bar_h + 1, bsz * p["lh"] * px)
        y = content.top()
        if p["title"]:
            qp.setPen(Qt.PenStyle.NoPen)
            for width, height, colour in ((0.42, max(2.0, bsz * 0.95 * px), t["acc"]),
                                          (0.28, bar_h, t["mut"])):
                qp.setBrush(qcolor(colour))
                w = content.width() * width
                qp.drawRoundedRect(QRectF(content.center().x() - w / 2, y + 4 * px, w, height),
                                   height / 2, height / 2)
                y += 4 * px + height + 8 * px
            y += 4 * px
        card_w = content.width()
        if p["card_width"] > 0:
            card_w = min(card_w, p["card_width"] * px)
        left = content.center().x() - card_w / 2
        pad_v = p["padding"] * px
        pad_h = max(4, p["padding"] - 4) * px
        gap = p["gap"] * px
        cards, image_rect, line_marks = [], None, []
        i = 0
        while i < 24:
            q_lines, a_lines, has_image = self.CARDS[i % len(self.CARDS)]
            inner_w = card_w - 2 * pad_h
            img = None
            if has_image:
                nat_h, aspect = self.IMAGE_PX
                h_css = min(nat_h, p["img"])
                w_css = h_css * aspect
                if w_css * px > inner_w:
                    w_css = inner_w / px
                    h_css = w_css / aspect
                img = (w_css * px, h_css * px)
            num_h = 13 * px if p["card_numbers"] else 0
            height = (2 * pad_v + num_h + (q_lines + a_lines) * pitch + 0.7 * pitch
                      + (img[1] + 0.5 * pitch if img else 0))
            if y + height > content.bottom() + 0.5:
                break
            card = QRectF(left, y, card_w, height)
            self._card(qp, card, p["style"], t, px)
            bands = []  # one band per line of text, for the line-height mark
            cy = y + pad_v
            inner_x = card.left() + pad_h
            if p["card_numbers"]:
                qp.setBrush(qcolor(t["mut"]))
                qp.drawRoundedRect(QRectF(inner_x, cy, 22 * px, max(1.4, 5 * px)), 1, 1)
                cy += num_h
            for n in range(q_lines):
                self._bar(qp, inner_x, cy, inner_w * self.BARS[(i + n) % len(self.BARS)], bar_h, pitch,
                          t["txt"], 150, bands)
                cy += pitch
            if img:
                cy += 0.25 * pitch
                rect = QRectF(card.center().x() - img[0] / 2, cy, img[0], img[1])
                image_rect = image_rect or rect
                self._picture(qp, rect, t)
                cy += img[1] + 0.25 * pitch
            qp.setPen(QPen(qcolor(t["div"]), 1))
            qp.drawLine(QPointF(inner_x, cy + 0.35 * pitch), QPointF(inner_x + inner_w, cy + 0.35 * pitch))
            cy += 0.7 * pitch
            first_answer = cy
            for n in range(a_lines):
                self._bar(qp, inner_x, cy, inner_w * self.BARS[(i + n + 3) % len(self.BARS)], bar_h, pitch,
                          t["txt"], 85, bands)
                cy += pitch
            if a_lines >= 2:
                line_marks.append((i, (first_answer, first_answer + pitch, card), bands))
            cards.append((card, QRectF(inner_x, y + pad_v, inner_w, height - 2 * pad_v)))
            y += height + gap
            i += 1
        gaps = [QRectF(left, a[0].bottom(), card_w, gap) for a, b in zip(cards, cards[1:])]
        # line height is marked on a card further down, away from the padding mark on the first
        lh_span, lh_bands = None, []
        if line_marks:
            _, lh_span, lh_bands = next((m for m in line_marks if m[0] >= 2), line_marks[0])
            card = lh_span[2]  # bands across the whole text width: the rhythm, not the words
            lh_bands = [QRectF(card.left() + pad_h, b.top(), card.width() - 2 * pad_h, b.height())
                        for b in lh_bands]
        number = None
        if p["numbers"]:
            w, h = max(10.0, 36 * px), max(1.6, 5 * px)
            number = QRectF(sheet.center().x() - w / 2, sheet.bottom() - bottom * scale / 2 - h / 2, w, h)
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(qcolor(t["mut"]))
            qp.drawRoundedRect(number, h / 2, h / 2)
        info_bar = None
        if info:  # the export info, small, in the bottom-right corner
            h = max(1.2, 4 * px)
            room = content.width() / 2 - (number.width() / 2 + 8 if number is not None else 0)
            w = max(8.0, min(200 * px, room))
            info_bar = QRectF(content.right() - w, sheet.bottom() - bottom * scale / 2 - h / 2, w, h)
            colour = qcolor(t["mut"])
            colour.setAlpha(150)
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(colour)
            qp.drawRoundedRect(info_bar, h / 2, h / 2)

        # what each option controls: areas to tint (and to point at), dimension lines, label anchors
        areas = {
            "margin": [QRectF(sheet.left(), sheet.top(), margin * scale, sheet.height()),
                       QRectF(content.right(), sheet.top(), margin * scale, sheet.height())],
            "top": [QRectF(sheet.left(), sheet.top(), sheet.width(), top * scale),
                    QRectF(sheet.left(), content.bottom(), sheet.width(), bottom * scale)],
            "gap": [g.adjusted(0, -1, 0, 1) if g.height() < 2 else g for g in gaps],
            # every other line: the rhythm of the line height, with a free line between two bands
            "lh": lh_bands[::2],
            "img": [image_rect] if image_rect is not None else [],
            # page numbers and export info are too small for a box: they light up themselves
            "page": [],
        }
        dims = []  # (key, start, end, anchor)
        x = sheet.right() - margin * scale / 2
        dims.append(("top", QPointF(x, sheet.top()), QPointF(x, content.top()),
                     QPointF(x, (sheet.top() + content.top()) / 2)))
        padding_ring = None
        if cards:
            card, inner = cards[0]
            padding_ring = QPainterPath()
            padding_ring.addRect(card)
            padding_ring.addRect(inner)
            padding_ring.setFillRule(Qt.FillRule.OddEvenFill)
            y = inner.top() + min(pitch, inner.height()) / 2
            dims.append(("padding", QPointF(inner.right(), y), QPointF(card.right(), y),
                         QPointF(card.right(), y)))
        if gaps:
            g = gaps[0]
            x = g.right() - g.width() * 0.12
            dims.append(("gap", QPointF(x, g.top()), QPointF(x, g.bottom()), QPointF(x, g.center().y())))
        if lh_span:
            y0, y1, card = lh_span
            x = card.right() - pad_h / 2
            dims.append(("lh", QPointF(x, y0), QPointF(x, y1), QPointF(x, (y0 + y1) / 2)))
        if image_rect is not None:
            x = image_rect.right() + max(3.0, 4 * px)
            dims.append(("img", QPointF(x, image_rect.top()), QPointF(x, image_rect.bottom()),
                         QPointF(x, image_rect.center().y())))
        starts = {}  # leaders that leave their mark sideways before running right
        if number is not None:
            anchor = QPointF(number.right() + 3, number.center().y())
            if info_bar is not None:  # run under the export info, not through it
                starts["numbers"] = QPointF(number.center().x(), number.bottom() + 1)
                lane = (max(number.bottom(), info_bar.bottom()) + 0.6 + sheet.bottom()) / 2
                anchor = QPointF(number.center().x(), lane)
            dims.append(("numbers", None, None, anchor))
        if info_bar is not None:
            dims.append(("info", None, None, QPointF(info_bar.right() + 3, info_bar.center().y())))
        # the side margin is measured where no other leader crosses the margin, so no two lines
        # ever run along each other
        taken = [anchor.y() for _, _, _, anchor in dims]
        y = max((content.top() + content.height() * k / 12 for k in range(2, 11)),
                key=lambda c: (min([abs(c - t) for t in taken] or [1e9]), -abs(c - content.center().y())))
        dims.append(("margin", QPointF(content.right(), y), QPointF(sheet.right(), y),
                     QPointF((content.right() + sheet.right()) / 2, y)))
        self._lanes = (y, taken)

        active = any(self._level(k) == 2 for k in notes) or self._focus == "page"
        shapes = {1: QPainterPath(), 2: QPainterPath()}
        for key in list(areas) + ["padding"]:
            level = self._level(key)
            if not level:
                continue
            shape = QPainterPath()
            shape.setFillRule(Qt.FillRule.WindingFill)
            for rect in areas.get(key, []):
                shape.addRect(rect)
            if key == "padding" and padding_ring is not None:
                shape = shape.united(padding_ring)
            shapes[level] = shapes[level].united(shape)
        # the hovered area keeps a clear gap from the edited one, and every area has an edge,
        # so neighbouring marks never run together
        halo = QPainterPathStroker()
        halo.setWidth(5)
        shapes[1] = shapes[1].subtracted(shapes[2].united(halo.createStroke(shapes[2])))
        for level in (1, 2):
            if shapes[level].isEmpty():
                continue
            fill, edge = qcolor(pal["accent_soft"]), QColor(accent)
            if level == 1:
                fill.setAlpha(int(fill.alpha() * 0.6))
            edge.setAlpha(200 if level == 2 else 110)
            qp.setPen(QPen(edge, 1))
            qp.setBrush(fill)
            qp.drawPath(shapes[level])
        for key, mark in (("numbers", number), ("info", info_bar)):
            level = self._level(key)
            if mark is not None and level:
                lit = QColor(accent)
                lit.setAlpha(255 if level == 2 else 150)
                qp.setPen(Qt.PenStyle.NoPen)
                qp.setBrush(lit)
                grown = mark.adjusted(-0.6, -0.6, 0.6, 0.6)
                qp.drawRoundedRect(grown, grown.height() / 2, grown.height() / 2)
        if self._level("page"):
            qp.setPen(QPen(accent, 2 if self._level("page") == 2 else 1))
            qp.setBrush(Qt.BrushStyle.NoBrush)
            qp.drawRoundedRect(sheet, 2, 2)
        for key, a, b, _ in dims:
            if a is not None and key in notes:
                self._dimension(qp, a, b, accent, self._level(key), active)

        # labels beside the sheet, in the order of what they point at, never overlapping
        rows = sorted((anchor.y(), key, anchor) for key, _, _, anchor in dims if key in notes)
        line_h = self.NOTE_PX + 7  # a label's height
        step = line_h + self.LABEL_GAP  # labels never touch, highlighted or not
        ys = self._stack([want for want, _, _ in rows], step, line_h / 2 + 2, self.height() - line_h / 2 - 2)
        hits = []
        self._labels = []  # drawn label boxes (the checks make sure they never overlap)
        label_x = sheet.right() + 20
        metrics = QFontMetricsF(self._note_font(True))
        for (_, key, anchor), ly in zip(rows, ys):
            level = self._level(key)
            lead = QColor(accent) if level else qcolor(pal["secondary"])
            lead.setAlpha(255 if level else (60 if active else 120))
            qp.setPen(QPen(lead, 1.2 if level == 2 else 0.8))
            start = starts.get(key, anchor)
            path = QPainterPath(start)
            path.lineTo(anchor)
            path.lineTo(QPointF(max(anchor.x(), sheet.right()) + 6, anchor.y()))
            path.lineTo(QPointF(label_x - 4, ly))
            qp.setBrush(Qt.BrushStyle.NoBrush)
            qp.drawPath(path)
            qp.setPen(Qt.PenStyle.NoPen)
            qp.setBrush(lead)
            qp.drawEllipse(start, 2.0 if level == 2 else 1.6, 2.0 if level == 2 else 1.6)
            text = notes[key]
            box = QRectF(label_x, ly - line_h / 2, metrics.horizontalAdvance(text) + 12, line_h)
            qp.setFont(self._note_font(level == 2))
            if level == 2:  # the option being edited: a filled label
                qp.setBrush(accent)
                qp.drawRoundedRect(box, line_h / 2, line_h / 2)
                qp.setPen(QColor("#ffffff"))
            elif level == 1:
                qp.setBrush(qcolor(pal["accent_soft"]))
                qp.drawRoundedRect(box, line_h / 2, line_h / 2)
                qp.setPen(accent)
            else:
                colour = qcolor(pal["text"])
                if active:
                    colour.setAlpha(110)
                qp.setPen(colour)
            qp.drawText(box, Qt.AlignmentFlag.AlignCenter, text)
            self._labels.append(box)
            hits.append((box.adjusted(-4, -1, 4, 1), key))

        caption = QRectF(sheet.left(), sheet.bottom() + 6, sheet.width(), 16)  # stays under the sheet
        page_level = self._level("page")
        qp.setFont(self._note_font(page_level == 2))
        qp.setPen(accent if page_level else qcolor(pal["secondary"]))
        qp.drawText(caption, Qt.AlignmentFlag.AlignCenter,
                    "{} · {:g} × {:g} mm".format(p["name"], pw, ph))
        qp.end()

        # what the pointer can pick on the sheet: small, specific marks before the large areas
        for key, mark in (("numbers", number), ("info", info_bar)):
            if mark is not None:
                hits.append((mark.adjusted(-3, -3, 3, 3), key))
        for key in ("img", "gap"):
            hits.extend((rect.adjusted(-2, -2, 2, 2), key) for rect in areas[key])
        if lh_span:
            y0, y1, card = lh_span
            hits.append((QRectF(card.left(), y0, card.width(), y1 - y0), "lh"))
        if cards:
            card, inner = cards[0]
            for rect in (QRectF(card.left(), card.top(), card.width(), inner.top() - card.top()),
                         QRectF(card.left(), inner.bottom(), card.width(), card.bottom() - inner.bottom()),
                         QRectF(card.left(), card.top(), inner.left() - card.left(), card.height()),
                         QRectF(inner.right(), card.top(), card.right() - inner.right(), card.height())):
                hits.append((rect.adjusted(-1, -1, 1, 1), "padding"))
        for key in ("top", "margin"):
            hits.extend((rect, key) for rect in areas[key])
        hits.append((caption, "page"))
        self._hits = [(rect, key) for rect, key in hits if key in notes or key == "page"]

    @staticmethod
    def _stack(wanted, step, low, high):
        """Positions as close as possible to `wanted` (sorted), at least `step` apart, within
        [low, high]; when they cannot all fit the step shrinks evenly instead of overlapping."""
        if not wanted:
            return []
        if len(wanted) > 1:
            step = min(step, (high - low) / (len(wanted) - 1))
        ys = []
        for want in wanted:
            ys.append(max(want, low, ys[-1] + step if ys else low))
        limit = high
        for n in range(len(ys) - 1, -1, -1):  # push back up from the bottom
            ys[n] = min(ys[n], limit)
            limit = ys[n] - step
        return ys

    @staticmethod
    def _dimension(qp, a, b, accent, level, dimmed):
        """A measured span: a line with short end ticks across it."""
        colour = QColor(accent)
        colour.setAlpha(255 if level else (70 if dimmed else 150))
        qp.setPen(QPen(colour, (1.6, 1.2, 0.9)[2 - level] if level else 0.9))
        qp.drawLine(a, b)
        dx, dy = b.x() - a.x(), b.y() - a.y()
        length = max(1e-6, (dx * dx + dy * dy) ** 0.5)
        tick = 3.5 if level == 2 else 2.5
        nx, ny = -dy / length * tick, dx / length * tick
        for point in (a, b):
            qp.drawLine(QPointF(point.x() - nx, point.y() - ny), QPointF(point.x() + nx, point.y() + ny))

    @staticmethod
    def _bar(qp, x, y, width, bar_h, pitch, colour, alpha, bands):
        c = qcolor(colour)
        c.setAlpha(alpha)
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(c)
        qp.drawRoundedRect(QRectF(x, y + (pitch - bar_h) / 2, width, bar_h), bar_h / 2, bar_h / 2)
        bands.append(QRectF(x - 1, y, width + 2, pitch))

    @staticmethod
    def _picture(qp, rect, t):
        qp.setPen(QPen(qcolor(t["brd"]), 1))
        qp.setBrush(qcolor(t["alt"]))
        qp.drawRect(rect)
        qp.setPen(Qt.PenStyle.NoPen)
        qp.setBrush(qcolor(t["mut"]))
        w, h = rect.width(), rect.height()
        hills = QPainterPath()
        hills.moveTo(rect.left() + w * 0.12, rect.bottom() - h * 0.14)
        hills.lineTo(rect.left() + w * 0.38, rect.top() + h * 0.42)
        hills.lineTo(rect.left() + w * 0.55, rect.top() + h * 0.64)
        hills.lineTo(rect.left() + w * 0.68, rect.top() + h * 0.5)
        hills.lineTo(rect.left() + w * 0.88, rect.bottom() - h * 0.14)
        hills.closeSubpath()
        qp.drawPath(hills)

    @staticmethod
    def _card(qp, card, style, t, px):
        radius = max(1.5, 12 * px)
        fill, line = qcolor(t["card"]), QPen(qcolor(t["brd"]), 1)
        qp.setBrush(fill)
        if style == 0:  # rounded
            qp.setPen(line)
            qp.drawRoundedRect(card, radius, radius)
        elif style == 1:  # sharp
            qp.setPen(line)
            qp.drawRect(card)
        elif style == 2:  # separator: a rule underneath
            qp.setPen(Qt.PenStyle.NoPen)
            qp.drawRect(card)
            qp.setPen(QPen(qcolor(t["accent_brd"]), 1.5))
            qp.drawLine(card.bottomLeft(), card.bottomRight())
        elif style == 3:  # double border
            qp.setPen(QPen(qcolor(t["accent_brd"]), 1))
            qp.drawRoundedRect(card, radius, radius)
            qp.setBrush(Qt.BrushStyle.NoBrush)
            qp.drawRoundedRect(card.adjusted(2.2, 2.2, -2.2, -2.2), radius - 1.5, radius - 1.5)
        else:  # none
            qp.setPen(Qt.PenStyle.NoPen)
            qp.drawRect(card)
        qp.setPen(Qt.PenStyle.NoPen)


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
