"""Guided filtering: a rule editor (Mail rules / Finder smart folder style) and a quick menu.

Both produce an ordinary Anki search, so the filter field keeps working as before and anything
typed by hand still works. A rule is a dict {"prop", "op", "value", "num", "extra"}; `term()`
turns one rule into Anki search syntax, `build_query()` joins them with AND or OR.
"""
import re

from aqt.qt import (
    QComboBox, QCompleter, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSizePolicy, QSpinBox, Qt, QTimer, QVBoxLayout, QWidget,
)

from . import macui

try:
    from anki.collection import SearchNode
except ImportError:  # pragma: no cover - every supported Anki has it
    SearchNode = None


# ------------------------------------------------------------------ properties
# key, group, kind. Kinds: choice (fixed list), list (names from the collection), tag, field,
# text, days, rated, due, compare, custom.
CRITERIA = [
    ("state", "flt_g_cards", "choice"),
    ("flag", "flt_g_cards", "choice"),
    ("tag", "flt_g_cards", "tag"),
    ("notetype", "flt_g_cards", "list"),
    ("template", "flt_g_cards", "list"),
    ("field", "flt_g_content", "field"),
    ("text", "flt_g_content", "text"),
    ("added", "flt_g_dates", "days"),
    ("edited", "flt_g_dates", "days"),
    ("rated", "flt_g_dates", "rated"),
    ("introduced", "flt_g_dates", "days"),
    ("due", "flt_g_dates", "due"),
    ("ivl", "flt_g_stats", "compare"),
    ("reps", "flt_g_stats", "compare"),
    ("lapses", "flt_g_stats", "compare"),
    ("ease", "flt_g_stats", "compare"),
    ("fsrs_d", "flt_g_fsrs", "compare"),
    ("fsrs_s", "flt_g_fsrs", "compare"),
    ("fsrs_r", "flt_g_fsrs", "compare"),
    ("custom", "flt_g_adv", "custom"),
]
KIND = {key: kind for key, _, kind in CRITERIA}

STATES = [("due", "flt_v_due"), ("new", "flt_v_new"), ("learn", "flt_v_learn"),
          ("review", "flt_v_review"), ("suspended", "flt_v_suspended"), ("buried", "flt_v_buried")]
FLAGS = [("1", "flt_f_red", "#e5534b"), ("2", "flt_f_orange", "#ef8b2c"),
         ("3", "flt_f_green", "#47b35b"), ("4", "flt_f_blue", "#3b82f6"),
         ("5", "flt_f_pink", "#e879c9"), ("6", "flt_f_turquoise", "#2dbfae"),
         ("7", "flt_f_purple", "#9b5de5"), ("any", "flt_f_any", None), ("0", "flt_f_none", None)]
ANSWERS = [("", "flt_a_any"), ("1", "flt_a_again"), ("2", "flt_a_hard"), ("3", "flt_a_good"),
           ("4", "flt_a_easy")]

OPS = {
    "choice": ["is", "is_not"],
    "list": ["is", "is_not"],
    "tag": ["has", "has_not", "no_tags"],
    "field": ["contains", "not_contains", "exact", "starts", "empty", "not_empty"],
    "text": ["contains", "not_contains", "word"],
    "days": ["in_last", "not_in_last"],
    "rated": ["in_last", "not_in_last"],
    "due": ["overdue", "within", "on"],
    "compare": ["lt", "le", "eq", "ge", "gt"],
    "custom": ["matches"],
}
COMPARE = {"lt": "<", "le": "<=", "eq": "=", "ge": ">=", "gt": ">"}

# prop:<name>, unit, scale applied to the number the user types, spin range, default
PROPS = {
    "ivl": ("ivl", "flt_u_days", 1, (0, 36500), 21),
    "reps": ("reps", "", 1, (0, 100000), 5),
    "lapses": ("lapses", "", 1, (0, 1000), 3),
    "ease": ("ease", "%", 0.01, (100, 1000), 200),
    "fsrs_d": ("d", "%", 0.01, (0, 100), 70),
    "fsrs_s": ("s", "flt_u_days", 1, (0, 36500), 30),
    "fsrs_r": ("r", "%", 0.01, (0, 100), 80),
}
DAY_DEFAULTS = {"added": 7, "edited": 7, "rated": 1, "introduced": 30, "due": 7}


def _quoted(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _wild_escape(text):
    """Escape Anki's wildcards (* and _) and the escape character itself."""
    return re.sub(r'([\\*_"])', r"\\\1", text)


class Escaper:
    """Search syntax for names and text: Anki's own builder when there is a collection."""

    def __init__(self, col=None):
        self.col = col

    def _node(self, **kw):
        if self.col is None or SearchNode is None:
            return None
        try:
            return self.col.build_search_string(SearchNode(**kw))
        except Exception:
            return None

    def tag(self, name):
        return self._node(tag=name) or "tag:" + _wild_escape(name)

    def note(self, name):
        return self._node(note=name) or _quoted("note:" + _wild_escape(name))

    def text(self, value):
        return self._node(literal_text=value) or _quoted(_wild_escape(value))

    @staticmethod
    def template(name):
        return _quoted("card:" + _wild_escape(name))

    @staticmethod
    def field(name, pattern):
        return _quoted("{}:{}".format(name.replace(":", "\\:"), pattern))


def _num(value):
    return "{:g}".format(round(value, 4))


def term(rule, esc):
    """One rule -> one Anki search term ("" when it is incomplete)."""
    prop, op = rule.get("prop"), rule.get("op")
    value = rule.get("value")
    value = value.strip() if isinstance(value, str) else value
    num = rule.get("num")
    neg = "-" if op in ("is_not", "has_not", "not_contains", "not_in_last") else ""
    kind = KIND.get(prop)
    if kind is None:
        return ""
    if prop == "state":
        return neg + "is:" + value if value else ""
    if prop == "flag":
        if value == "any":
            return ("" if neg else "-") + "flag:0"
        return neg + "flag:" + value if value else ""
    if prop == "tag":
        if op == "no_tags":
            return "tag:none"
        return neg + esc.tag(value) if value else ""
    if prop == "notetype":
        return neg + esc.note(value) if value else ""
    if prop == "template":
        return neg + esc.template(value) if value else ""
    if prop == "field":
        field = rule.get("extra") or ""
        if not field:
            return ""
        if op == "empty":
            return esc.field(field, "")
        if op == "not_empty":
            return esc.field(field, "_*")
        if not value:
            return ""
        text = _wild_escape(value)
        pattern = {"exact": text, "starts": text + "*"}.get(op, "*" + text + "*")
        return neg + esc.field(field, pattern)
    if prop == "text":
        if not value:
            return ""
        if op == "word":
            return "w:" + (_quoted(_wild_escape(value)) if " " in value else _wild_escape(value))
        return neg + esc.text(value)
    if prop in ("added", "edited", "introduced"):
        return neg + "{}:{}".format(prop, max(1, int(num or 1)))
    if prop == "rated":
        days = max(1, min(365, int(num or 1)))
        answer = rule.get("extra") or ""
        return neg + "rated:{}{}".format(days, ":" + answer if answer else "")
    if prop == "due":
        if op == "overdue":
            return "prop:due<0"
        days = max(0, int(num or 0))
        return "prop:due={}".format(days) if op == "on" else "prop:due<={}".format(days)
    if prop in PROPS:
        name, _, scale, _, _ = PROPS[prop]
        return "prop:{}{}{}".format(name, COMPARE.get(op, ">="), _num(float(num or 0) * scale))
    if prop == "custom":
        return "({})".format(value) if value else ""
    return ""


def build_query(rules, match_all, esc):
    terms = [t for t in (term(r, esc) for r in rules) if t]
    if len(terms) < 2:
        return terms[0] if terms else ""
    return (" " if match_all else " OR ").join(terms)


def default_rule(prop="tag"):
    kind = KIND[prop]
    rule = {"prop": prop, "op": OPS[kind][0], "value": "", "num": 0, "extra": ""}
    if prop == "state":
        rule["value"] = "due"
    elif prop == "flag":
        rule["value"] = "1"
    elif prop in DAY_DEFAULTS:
        rule["num"] = DAY_DEFAULTS[prop]
        if prop == "due":
            rule["op"] = "within"
    elif prop in PROPS:
        rule["num"] = PROPS[prop][4]
        rule["op"] = "ge" if prop in ("ivl", "reps", "lapses", "fsrs_d", "fsrs_s") else "lt"
    return rule


# ------------------------------------------------------------------ quick menu
def fill_quick_menu(menu, ctx, tr, add_term, open_builder, clear):
    """Populate the menu of the filter field. `ctx` provides tags() / notetypes() of the deck."""
    menu.clear()
    pal = ctx.palette
    build = menu.addAction(tr("btn_build_filter"))
    build.triggered.connect(open_builder)
    menu.addSeparator()

    def sub(title):
        m = menu.addMenu(title)
        macui.round_popup(m, pal)
        return m

    def item(m, label, query, icon=None):
        act = m.addAction(label)
        if icon is not None:
            act.setIcon(icon)
        act.triggered.connect(lambda _=False, q=query: add_term(q))

    m = sub(tr("flt_p_state"))
    for key, label in STATES:
        item(m, tr(label), "is:" + key)
    m.addSeparator()
    item(m, tr("flt_q_not_suspended"), "-is:suspended")

    m = sub(tr("flt_p_flag"))
    for key, label, colour in FLAGS:
        if key == "any":
            m.addSeparator()
        query = "-flag:0" if key == "any" else "flag:" + key
        item(m, tr(label), query, macui.dot_icon(colour) if colour else None)

    m = sub(tr("flt_p_tag"))
    item(m, tr("flt_q_marked"), "tag:marked")
    item(m, tr("flt_q_leech"), "tag:leech")
    item(m, tr("flt_o_no_tags"), "tag:none")
    tags = [t for t, _ in ctx.tags() if t.lower() not in ("marked", "leech")][:30]
    if tags:
        m.addSeparator()
        for tag in tags:
            item(m, tag, ctx.esc.tag(tag))

    names = ctx.notetypes()
    if names:
        m = sub(tr("flt_p_notetype"))
        for name in names[:30]:
            item(m, name, ctx.esc.note(name))

    m = sub(tr("flt_p_added"))
    item(m, tr("flt_q_today"), "added:1")
    item(m, tr("flt_q_last7"), "added:7")
    item(m, tr("flt_q_last30"), "added:30")

    m = sub(tr("flt_p_rated"))
    item(m, tr("flt_q_today"), "rated:1")
    item(m, tr("flt_q_last7"), "rated:7")
    m.addSeparator()
    item(m, tr("flt_q_again_today"), "rated:1:1")
    item(m, tr("flt_q_again_7"), "rated:7:1")

    m = sub(tr("flt_q_hard"))
    item(m, tr("flt_q_lapses"), "prop:lapses>=3")
    item(m, tr("flt_q_ease"), "prop:ease<2")
    m.addSeparator()
    item(m, tr("flt_q_fsrs_d"), "prop:d>0.7")
    item(m, tr("flt_q_fsrs_r"), "prop:r<0.8")

    menu.addSeparator()
    clear_act = menu.addAction(tr("flt_clear"))
    clear_act.setEnabled(ctx.has_filter())
    clear_act.triggered.connect(clear)


def add_term_to(text, query):
    """Append `query` to an existing filter (AND), unless it is already there."""
    text = (text or "").strip()
    if not text:
        return query
    if query in text.split():
        return text
    if re.search(r"\bOR\b", text):  # keep an OR filter intact: (a OR b) new
        text = "({})".format(text)
    return "{} {}".format(text, query)


# ------------------------------------------------------------------ builder window
class _Combo(QComboBox):
    def __init__(self, pal):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._pal = pal

    def wheelEvent(self, e):
        # the wheel belongs to the list of rules: a pop-up that kept the focus after a choice used to
        # change its selection (and rebuild its row) while the list was being scrolled
        e.ignore()

    def polish(self):
        macui.round_popup(self, self._pal)
        return self

    def showPopup(self):
        # pop-ups sized to their contents got a list narrower than the button on macOS, which
        # elided the entries ("all" vanished from the Match pop-up)
        view = self.view()
        view.setMinimumWidth(max(self.width(), view.sizeHintForColumn(0) + 32))
        super().showPopup()


class _Spin(QSpinBox):
    def wheelEvent(self, e):
        e.ignore()  # see _Combo.wheelEvent


class _Row(QWidget):
    """[property] [field] [condition] [value ...]  (−) (+)"""

    def __init__(self, dlg, rule):
        super().__init__()
        self.dlg = dlg
        self.tr = dlg.tr
        self.setObjectName("FilterRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        ly = QHBoxLayout(self)
        ly.setContentsMargins(12, 7, 8, 7)
        ly.setSpacing(8)
        self.prop = _Combo(dlg.pal)
        last_group = None
        for key, group, _ in CRITERIA:
            if last_group is not None and group != last_group:
                self.prop.insertSeparator(self.prop.count())
            last_group = group
            self.prop.addItem(self.tr("flt_p_" + key), key)
        self.prop.polish()
        self.prop.setMinimumWidth(170)
        ly.addWidget(self.prop)
        self.slot = QHBoxLayout()
        self.slot.setSpacing(8)
        ly.addLayout(self.slot, 1)
        self.minus = QPushButton()
        self.plus = QPushButton()
        for btn, glyph, tip in ((self.minus, "minus_circle", "tip_flt_remove"),
                                (self.plus, "plus_circle", "tip_flt_add")):
            btn.setObjectName("Plain")
            btn.setIcon(macui.glyph_icon(glyph, dlg.pal))
            btn.setFixedSize(24, 24)
            btn.setToolTip(self.tr(tip))
            btn.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            ly.addWidget(btn)
        self.minus.clicked.connect(lambda: dlg.remove_row(self))
        self.plus.clicked.connect(lambda: dlg.add_row(after=self))
        self.prop.setCurrentIndex(max(0, self.prop.findData(rule["prop"])))
        self.prop.currentIndexChanged.connect(self._prop_changed)
        self._build(rule)

    # ------------------------------------------------------------ editing
    def _prop_changed(self, *_):
        self._build(default_rule(self.prop.currentData()))
        self.dlg.changed()

    def _clear(self):
        while self.slot.count():
            item = self.slot.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self.op = self.pre = self.value = self.num = self.extra = None

    def _combo(self, items, current=None, min_width=0, editable=False):
        combo = _Combo(self.dlg.pal)
        combo.setEditable(editable)
        for item in items:
            label, data = (item, item) if isinstance(item, str) else item
            combo.addItem(label, data)
        if editable:
            combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            combo.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            combo.setEditText(current or "")
            combo.lineEdit().textChanged.connect(self.dlg.changed)
        elif current is not None:
            combo.setCurrentIndex(max(0, combo.findData(current)))
        if min_width:
            combo.setMinimumWidth(min_width)
        combo.currentIndexChanged.connect(self.dlg.changed)
        self.slot.addWidget(combo.polish())
        return combo

    def _line(self, text, placeholder="", min_width=160):
        edit = QLineEdit(text or "")
        edit.setPlaceholderText(placeholder)
        edit.setMinimumWidth(min_width)
        edit.textChanged.connect(self.dlg.changed)
        self.slot.addWidget(edit, 1)
        return edit

    def _spin(self, value, lo, hi, suffix=""):
        spin = _Spin()
        spin.setRange(lo, hi)
        spin.setValue(int(value))
        spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        spin.setFixedWidth(84)
        spin.valueChanged.connect(self.dlg.changed)
        self.slot.addWidget(spin)
        if suffix:
            unit = QLabel(suffix)
            unit.setObjectName("Secondary")
            self.slot.addWidget(unit)
        return spin

    def _build(self, rule):
        self._clear()
        prop = rule["prop"]
        kind = KIND[prop]
        ctx = self.dlg.ctx
        if kind == "field":
            self.pre = self._combo(ctx.fields(), rule.get("extra") or None, 120)
        self.op = self._combo([(self.tr("flt_o_" + op), op) for op in OPS[kind]], rule["op"])
        if kind == "custom":
            self.op.setVisible(False)
        if prop == "state":
            self.value = self._combo([(self.tr(l), k) for k, l in STATES], rule["value"])
        elif prop == "flag":
            self.value = self._combo([(self.tr(l), k) for k, l, _ in FLAGS], rule["value"])
            for i, (_, _, colour) in enumerate(FLAGS):
                if colour:
                    self.value.setItemIcon(i, macui.dot_icon(colour))
        elif prop == "tag":
            self.value = self._combo([t for t, _ in ctx.tags()], rule["value"], 180, editable=True)
        elif prop == "notetype":
            self.value = self._combo(ctx.notetypes(), rule["value"] or None, 180)
        elif prop == "template":
            self.value = self._combo(ctx.templates(), rule["value"] or None, 150)
        elif kind in ("field", "text"):
            self.value = self._line(rule["value"], self.tr("flt_ph_text"))
        elif kind in ("days", "rated", "due"):
            hi = 365 if kind == "rated" else 36500
            self.num = self._spin(rule["num"] or DAY_DEFAULTS.get(prop, 1), 0 if kind == "due" else 1,
                                  hi, self.tr("flt_u_days"))
            if kind == "rated":
                self.extra = self._combo([(self.tr(l), k) for k, l in ANSWERS], rule.get("extra") or "")
        elif kind == "compare":
            _, unit, _, (lo, hi), default = PROPS[prop]
            self.num = self._spin(rule["num"] if rule["num"] else default, lo, hi,
                                  self.tr(unit) if unit.startswith("flt_") else unit)
        elif kind == "custom":
            self.value = self._line(rule["value"], self.tr("ph_filter"), 260)
        if kind not in ("field", "text", "custom"):
            self.slot.addStretch(1)
        self.op.currentIndexChanged.connect(self._sync)
        self._sync()

    def _sync(self, *_):
        """Hide inputs a condition does not use (e.g. 'is empty', 'is overdue', 'has no tags')."""
        op = self.op.currentData() if self.op else None
        if self.value is not None:
            self.value.setVisible(op not in ("empty", "not_empty", "no_tags"))
        if self.num is not None and KIND[self.prop.currentData()] == "due":
            self.num.setVisible(op != "overdue")
            unit = self.slot.itemAt(self.slot.indexOf(self.num) + 1)
            if unit is not None and unit.widget() is not None:
                unit.widget().setVisible(op != "overdue")

    def rule(self):
        def val(w):
            if w is None:
                return ""
            if isinstance(w, QLineEdit):
                return w.text()
            if w.isEditable():
                return w.currentText()
            data = w.currentData()
            return data if data is not None else w.currentText()

        return {
            "prop": self.prop.currentData(),
            "op": self.op.currentData() if self.op else "",
            "value": val(self.value),
            "num": self.num.value() if self.num is not None else 0,
            "extra": val(self.pre) if self.pre is not None else val(self.extra),
        }


class FilterBuilderDialog(QDialog):
    """Rules -> Anki search, with the matching card count and the search itself shown live."""

    def __init__(self, parent, ctx, tr, deck_name, rules=None, match_all=True):
        super().__init__(parent)
        self.ctx = ctx
        self.tr = tr
        self.pal = ctx.palette
        self.query = ""
        self.setObjectName("PdfferWindow")  # same window background as the export window
        self.setWindowTitle(tr("flt_title"))
        self.setMinimumWidth(680)
        self.resize(760, 460)
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(10)

        title = QLabel(tr("flt_title"))
        f = title.font()
        f.setPointSize(f.pointSize() + 3)
        f.setBold(True)
        title.setFont(f)
        root.addWidget(title)
        intro = QLabel(tr("flt_intro").format(deck=deck_name))
        intro.setObjectName("Secondary")
        intro.setWordWrap(True)
        root.addWidget(intro)

        match = QHBoxLayout()
        match.setSpacing(6)
        match.addWidget(QLabel(tr("flt_match_pre")))
        self.match = _Combo(self.pal)
        self.match.addItem(tr("flt_all"), True)
        self.match.addItem(tr("flt_any"), False)
        self.match.setCurrentIndex(0 if match_all else 1)
        self.match.currentIndexChanged.connect(self.changed)
        match.addWidget(self.match.polish())
        match.addWidget(QLabel(tr("flt_match_post")))
        match.addStretch(1)
        root.addLayout(match)

        self.table = macui.RoundedFrame("table", "box_border", 8)
        self.table.setObjectName("Table")
        self.rows_ly = QVBoxLayout(self.table)
        self.rows_ly.setContentsMargins(0, 0, 0, 0)
        self.rows_ly.setSpacing(0)
        holder = QWidget()
        holder.setObjectName("Page")
        hl = QVBoxLayout(holder)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self.table)
        hl.addStretch(1)
        scroll = QScrollArea()
        scroll.setObjectName("PageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(holder)
        root.addWidget(scroll, 1)

        q_row = QHBoxLayout()
        q_row.setSpacing(8)
        q_lbl = QLabel(tr("flt_query"))
        q_lbl.setObjectName("Secondary")
        q_row.addWidget(q_lbl)
        self.query_label = QLabel("")
        self.query_label.setObjectName("QueryLabel")
        self.query_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.query_label.setWordWrap(True)
        self.query_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        q_row.addWidget(self.query_label, 1)
        root.addLayout(q_row)
        self.count_label = QLabel("")
        self.count_label.setObjectName("CountLabel")
        root.addWidget(self.count_label)

        buttons = QHBoxLayout()
        clear = QPushButton(tr("btn_flt_clear"))
        clear.setAutoDefault(False)
        clear.clicked.connect(self.clear)
        buttons.addWidget(clear)
        buttons.addStretch(1)
        cancel = QPushButton(tr("btn_cancel"))
        cancel.setAutoDefault(False)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        self.apply_btn = QPushButton(tr("btn_flt_apply"))
        self.apply_btn.setObjectName("Primary")
        self.apply_btn.setDefault(True)
        self.apply_btn.clicked.connect(self.accept)
        buttons.addWidget(self.apply_btn)
        root.addLayout(buttons)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.refresh)
        self.rows = []
        for rule in (rules or [default_rule()]):
            self.add_row(rule=rule)
        self.refresh()

    # ------------------------------------------------------------ rows
    def add_row(self, after=None, rule=None):
        row = _Row(self, rule or default_rule())
        index = self.rows.index(after) + 1 if after in self.rows else len(self.rows)
        self.rows.insert(index, row)
        self.rows_ly.insertWidget(index, row)
        self._restripe()
        self.changed()
        return row

    def remove_row(self, row):
        if len(self.rows) == 1:
            row._build(default_rule(row.prop.currentData()))
        else:
            self.rows.remove(row)
            row.setParent(None)
            row.deleteLater()
        self._restripe()
        self.changed()

    def _restripe(self):
        for i, row in enumerate(self.rows):
            row.setProperty("last", i == len(self.rows) - 1)
            row.style().unpolish(row)
            row.style().polish(row)
            row.minus.setEnabled(len(self.rows) > 1 or bool(term(row.rule(), self.ctx.esc)))

    def clear(self):
        for row in self.rows[1:]:
            row.setParent(None)
            row.deleteLater()
        self.rows = self.rows[:1]
        self.rows[0].prop.setCurrentIndex(self.rows[0].prop.findData("tag"))
        self.rows[0]._build(default_rule())
        self._restripe()
        self.changed()

    # ------------------------------------------------------------ result
    def rules(self):
        return [row.rule() for row in self.rows]

    def match_all(self):
        return bool(self.match.currentData())

    def changed(self, *_):
        self._timer.start(220)

    def refresh(self):
        self.query = build_query(self.rules(), self.match_all(), self.ctx.esc)
        self.query_label.setText(self.query or self.tr("flt_query_none"))
        try:
            cards, notes = self.ctx.count(self.query)
        except Exception as e:
            self._count(self.tr("flt_invalid").format(err=str(e).splitlines()[0][:160]), True)
            self.apply_btn.setEnabled(False)
            return
        self.apply_btn.setEnabled(True)
        if cards:
            self._count(self.tr("deck_count").format(cards=cards, notes=notes), False)
        else:
            self._count(self.tr("flt_none"), True)
        for row in self.rows:
            row.minus.setEnabled(len(self.rows) > 1 or bool(term(row.rule(), self.ctx.esc)))

    def _count(self, text, error):
        self.count_label.setText(text)
        self.count_label.setProperty("error", bool(error))
        self.count_label.style().unpolish(self.count_label)
        self.count_label.style().polish(self.count_label)

    def accept(self):
        self._timer.stop()
        self.refresh()
        if self.apply_btn.isEnabled():
            super().accept()
