"""Settings persistence for AnkiPdffer.

Pure Python (no Qt/Anki imports) so it can be unit-tested headlessly.

File layout (settings.json, schema v2)::

    {
      "version": 2,
      "settings": {...},              # last used global options (autosaved)
      "fields":   {"<note type>": {"<field>": {...field config...}}},
      "presets":  {"<name>": {"settings": {...}, "fields": {...}}},
      "field_presets": {"<name>": {"fields": {"<field>": {...}}, "order": [{...}, ...]}},
      "window":   {"geometry": "<base64>"}
    }

The v1 format was a flat dict of the global options; it is migrated on load.
"""
import base64
import copy
import json
import os
import tempfile

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
    "top_margin": 15,
    "padding": 12,
    "min_gap": 8,
    "line_height": 1.40,
    "max_img": 240,
    "strip_html": False,
    "card_style": 0,
    "grid": False,
    "language": "en",
    "debug": True,
    "high_contrast": False,
    # v1.4
    "qa_layout": 0,       # 0 together, 1 questions then answers, 2 question page / answer page
    "cloze_mode": 3,      # 0 reveal, 1 hide, 2 hidden->revealed, 3 native (Anki: one card per cloze)
    "io_mode": 0,         # 0 all masks at once (one entry per note), 1 one card per mask
    "order": 0,           # 0 deck order, 1 creation date, 2 shuffle
    "page_numbers": False,
    "tab": 0,             # last tab shown in the window
    "export_dir": "",     # folder of the last export ("" = Desktop)
    "overview_button": True,  # "Export to PDF" button on Anki's deck screen
    "engine_state": "",   # last PDF engine check: "ok", "missing" or "" (never checked)
}

# Options that describe *this machine / session* rather than the look of an export.
# They are not part of presets and are left alone by "apply preset".
MACHINE_KEYS = ("language", "debug", "tab", "export_dir", "overview_button", "engine_state")

DEFAULT_FIELD_CONFIG = {
    "export": True,
    "section": 1,
    "size": 1,
    "bold": False,
    "label": True,
    "bg": 0,
    "color": 0,
    "align": 0,
    "italic": False,
    "underline": False,
}

_FIELD_LIMITS = {"section": 2, "size": 3, "bg": 7, "color": 6, "align": 3}


def coerce_settings(raw):
    """Return a complete, type-safe settings dict (unknown keys dropped)."""
    safe = dict(DEFAULT_SETTINGS)
    if not isinstance(raw, dict):
        return safe
    for key, default in DEFAULT_SETTINGS.items():
        if key not in raw:
            continue
        val = raw[key]
        try:
            if isinstance(default, bool):
                safe[key] = bool(val)
            elif isinstance(default, int):
                safe[key] = int(val)
            elif isinstance(default, float):
                safe[key] = float(val)
            else:
                safe[key] = val if isinstance(val, str) else default
        except (TypeError, ValueError):
            safe[key] = default
    return safe


def coerce_field_config(raw):
    safe = dict(DEFAULT_FIELD_CONFIG)
    if not isinstance(raw, dict):
        return safe
    for key, default in DEFAULT_FIELD_CONFIG.items():
        if key not in raw:
            continue
        try:
            if isinstance(default, bool):
                safe[key] = bool(raw[key])
            else:
                val = int(raw[key])
                safe[key] = max(0, min(_FIELD_LIMITS.get(key, val), val))
        except (TypeError, ValueError):
            safe[key] = default
    return safe


def _coerce_fields_map(raw):
    out = {}
    if not isinstance(raw, dict):
        return out
    for nt_name, fields in raw.items():
        if not isinstance(fields, dict):
            continue
        out[str(nt_name)] = {str(f): coerce_field_config(c) for f, c in fields.items()}
    return out


class SettingsStore:
    def __init__(self, path):
        self.path = path
        self.settings = dict(DEFAULT_SETTINGS)
        self.fields = {}
        self.presets = {}
        self.field_presets = {}
        self.window = {}
        self.load()

    # ------------------------------------------------------------------ io
    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, ValueError):
            return False
        if not isinstance(raw, dict):
            return False
        if raw.get("version") == 2 or "settings" in raw:
            self.settings = coerce_settings(raw.get("settings"))
            self.fields = _coerce_fields_map(raw.get("fields"))
            presets = raw.get("presets")
            self.presets = {}
            if isinstance(presets, dict):
                for name, body in presets.items():
                    if isinstance(body, dict):
                        self.presets[str(name)] = {
                            "settings": coerce_settings(body.get("settings")),
                            "fields": _coerce_fields_map(body.get("fields")),
                        }
            self.field_presets = {}
            fpresets = raw.get("field_presets")
            if isinstance(fpresets, dict):
                for name, body in fpresets.items():
                    if isinstance(body, dict):
                        fields = body.get("fields") if isinstance(body.get("fields"), dict) else {}
                        order = body.get("order") if isinstance(body.get("order"), list) else []
                        self.field_presets[str(name)] = {
                            "fields": {str(f): coerce_field_config(c) for f, c in fields.items()},
                            "order": [coerce_field_config(c) for c in order],
                        }
            window = raw.get("window")
            self.window = window if isinstance(window, dict) else {}
        else:  # v1: flat dict of global options
            self.settings = coerce_settings(raw)
        return True

    def save(self):
        """Atomic write; returns None on success or the error string."""
        payload = {
            "version": 2,
            "settings": self.settings,
            "fields": self.fields,
            "presets": self.presets,
            "field_presets": self.field_presets,
            "window": self.window,
        }
        directory = os.path.dirname(self.path) or "."
        try:
            fd, tmp = tempfile.mkstemp(prefix=".settings-", suffix=".tmp", dir=directory)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
        except OSError as e:
            try:
                os.remove(tmp)
            except (OSError, UnboundLocalError):
                pass
            return str(e)
        return None

    # ------------------------------------------------------------ settings
    def update_settings(self, values):
        self.settings = coerce_settings({**self.settings, **(values or {})})

    def reset_settings(self, keep_machine_keys=True):
        keep = {k: self.settings[k] for k in MACHINE_KEYS} if keep_machine_keys else {}
        self.settings = {**DEFAULT_SETTINGS, **keep}

    # -------------------------------------------------------------- fields
    def get_fields(self, nt_name):
        return {f: dict(c) for f, c in self.fields.get(nt_name, {}).items()}

    def set_field(self, nt_name, field, config):
        self.fields.setdefault(nt_name, {})[field] = coerce_field_config(config)

    def reset_fields(self, nt_name=None):
        if nt_name is None:
            self.fields = {}
        else:
            self.fields.pop(nt_name, None)

    # ------------------------------------------------------------- presets
    def preset_names(self):
        return sorted(self.presets, key=str.lower)

    def save_preset(self, name):
        name = (name or "").strip()
        if not name:
            return False
        shared = {k: v for k, v in self.settings.items() if k not in MACHINE_KEYS}
        self.presets[name] = {
            "settings": shared,
            "fields": copy.deepcopy(self.fields),
        }
        return True

    def apply_preset(self, name):
        body = self.presets.get(name)
        if not body:
            return False
        keep = {k: self.settings[k] for k in MACHINE_KEYS}
        self.settings = coerce_settings({**body["settings"], **keep})
        self.fields = copy.deepcopy(body["fields"])
        return True

    def delete_preset(self, name):
        return self.presets.pop(name, None) is not None

    # ------------------------------------------------------- field presets
    # A field preset is the look of one note type's fields (section, size, style, ...).
    # It can be applied to any note type: fields match by name first, then by position.
    def field_preset_names(self):
        return sorted(self.field_presets, key=str.lower)

    def save_field_preset(self, name, ordered_configs):
        """`ordered_configs`: [(field name, config), ...] in the note type's field order."""
        name = (name or "").strip()
        if not name or not ordered_configs:
            return False
        configs = [(str(f), coerce_field_config(c)) for f, c in ordered_configs]
        self.field_presets[name] = {
            "fields": {f: c for f, c in configs},
            "order": [c for _, c in configs],
        }
        return True

    def apply_field_preset(self, name, nt_name, field_names):
        """Copy the preset onto `nt_name`; returns how many fields were set (0 if unknown)."""
        body = self.field_presets.get(name)
        if not body:
            return 0
        applied = 0
        for i, field in enumerate(field_names):
            cfg = body["fields"].get(field)
            if cfg is None and i < len(body["order"]):
                cfg = body["order"][i]
            if cfg is not None:
                self.set_field(nt_name, field, cfg)
                applied += 1
        return applied

    def delete_field_preset(self, name):
        return self.field_presets.pop(name, None) is not None

    # -------------------------------------------------------------- window
    def set_geometry(self, raw_bytes):
        self.window["geometry"] = base64.b64encode(bytes(raw_bytes)).decode("ascii")

    def get_geometry(self):
        try:
            return base64.b64decode(self.window.get("geometry", ""))
        except (ValueError, TypeError):
            return b""
