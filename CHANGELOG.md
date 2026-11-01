# Changelog

All notable changes to the **AnkiPdffer Dev** add-on will be documented in this file.

## [1.4.0] - 2026-11-01

### Added
- **Question / answer layouts**: keep each card together, print all questions followed by an answer key, or put each card's question on one page and its answer on the next (worksheet / self-test style).
- **Image Occlusion pages**: export a page with every mask covering the image and a second page with the masks removed and numbered outlines drawn, either one entry per note (all masks at once) or one card per mask. Masks are drawn by the exporter itself, so rectangles, ellipses and polygons render without Anki's JavaScript.
- **Cloze modes**: reveal answers, hide them as `[...]` (or `[hint]`), show the hidden version followed by the revealed one, or keep Anki's native card-per-cloze rendering.
- **Note type editor**: the Fields tab edits one note type at a time, pre-selected from the card you are reviewing (or the deck's most used type). Any note type in the collection can be picked and edited, and each remembers its own field configuration (with *Reset*). Aligned columns with headers; fields that are not exported are greyed out.
- **Field presets**: save how a note type's fields look and apply it to any note type (fields are matched by name, then by position).
- **Presets**: save the current options and field settings under a name, apply or delete them later, and reset everything to the original defaults.
- **Filter, order and live count**: narrow an export with any Anki search (`tag:leech is:due`), order cards by deck, creation date or shuffle, and see "N cards · M notes" before exporting.
- **Page numbers** (`3 / 12`) in the PDF footer.
- **Interface languages**: Spanish, Portuguese, German, French, Italian, Russian, Chinese (Simplified) and Japanese, next to English and Polish. Missing strings fall back to English; new languages are added in `translations.py`.
- **Developer tooling** (`dev/`): headless regression checks, dialog screenshots and sample PDFs (`dev/dev.sh preview`), a throw-away Anki sandbox (`dev/dev.sh sandbox`), and `dev/dev.sh sync` to install the working tree into Anki.

### Changed
- **Redesigned window** in the classic macOS style: deck pop-ups and a search field in a toolbar, segmented tabs (Content · Appearance · Page · Fields · Settings) on an inset box, right-aligned forms, segmented controls instead of radio buttons, Mac pop-up buttons, a status footer with the card count, and a HUD-style progress panel. Light and dark mode follow Anki. Rounded corners, check boxes and pop-up buttons are drawn antialiased, so edges stay crisp on Retina and standard displays.
- **Responsive window**: its minimum size follows the content (about 580 × 430), forms never get clipped, field rows switch to two lines in narrow windows, and wide windows keep the table centred.
- **Keyboard shortcuts**: ⌘1–5 switch tabs, ⌘F focuses the filter, ⌘P previews, ⌘↩ exports, ⌘W closes; Return in the filter refreshes the card count. The last tab is remembered.
- **Settings are saved automatically** (debounced, atomic write) whenever an option changes and again when the window is hidden or closed, instead of only on some actions. The window size and position are remembered too. Existing `settings.json` files are migrated to the new format on first load.
- **One window**: *Tools → AnkiPdffer → Open export dialog…* and the quick-export shortcut restore the existing window (also when minimized) instead of opening another one. The window follows profile switches and language changes.
- Google Fonts are only requested when the Inter stack is selected, so exports with other fonts work offline.
- `release.sh` builds from a clean staging copy, ships every top-level module, defaults to the version in `manifest.json` and has a `--build-only` mode.

### Fixed
- Settings occasionally not surviving a switch between decks or pages.
- Notes with several cards (reversed, cloze, Image Occlusion) being exported more than once in Fields mode.
- `[sound:…]` / `[anki:play:…]` tags and Image Occlusion canvas/button markup leaking into exports.
- Field names and card labels not being HTML-escaped.
- Forced page breaks being ignored in the PDF because empty `div`s were hidden by the stylesheet.
- Temporary HTML files left behind after a Qt WebEngine fallback export.

## [1.3.4] - 2026-05-31

### Fixed
- WeasyPrint fontconfig lookup on macOS.

### Added
- PDF export attribution line.

## [1.3.3] - 2026-05-22

### Fixed
- Isolated the WeasyPrint subprocess from Anki and other add-on Python paths to avoid cross-add-on `PIL` import failures.
- Restored natural PDF card ordering and improved compact layout pagination for long cards.
- Added the full Anki deck path under the export title and improved export path logging.
- Fixed malformed CSS sanitization rules in generated PDF HTML.

## [1.3.2] - 2026-05-19

### Changed
- **Package Size Optimization**: Pruned unneeded `.c` source files, unused `pyphen` language dictionaries (keeping only English and Polish), and `.dist-info` pip metadata. This reduces the final `.ankiaddon` package size from **11.2 MB** down to **8.3 MB** (~25% file size reduction).

## [1.3.1] - 2026-05-19

### Fixed
- **Menu Label**: Fixed the root menu name to be simply `"AnkiPdffer"` instead of `"AnkiPdffer Dev (Branch)"` for correct production display.
- **Dynamic Version Indicator**: Replaced the hardcoded `"v 1.2"` string in the dialog window footer with a dynamic loader that reads directly from `manifest.json`.

## [1.3.0] - 2026-05-19

### Added
- **Determinate Animated Loader & Overlay**: Smooth progress-tracking animated loading screen that triggers on export, showing a determinate percentage and a modern animated Braille spinner (`⠋`, `⠙`, `⠹`...) next to the status message.
- **Electric Blue Theme Palette**: Re-designed color scheme to feature `#101010` Slate dark mode background and `#fcfcfc` light mode background with gorgeous Electric Blue (`#3b82f6` / `#2563eb`) accents.
- **High-Fidelity Custom Scrollbars**: 6px-wide rounded vertical scrollbars that cleanly blend into the UI canvas.
- **Active-Left Sidebar Highlight Indicator**: Custom styling for the navigation sidebar that highlights the active tab with an elegant 3px vertical blue stripe on the left edge.

### Fixed
- **Radio Buttons & Checkboxes Checked Rendering**: Replaced standard checked markers with high-fidelity `background-image: qradialgradient` overlays to resolve native rendering issues on macOS/Qt.
- **Night Mode Detection**: Updated fallback night mode checking to support various Anki versions using primary `mw.pm.night_mode()` detection.
- **NameError `is_dark` Exception**: Resolved a crash inside `_create_busy_overlay` due to `is_dark` referencing an undefined name.
- **KeyError Curly Braces Exception**: Escaped all literal curly braces in sidebar and progress bar stylesheets (`{` and `}` to `{{` and `}}`) to prevent template string `.format()` interpolation conflicts.
- **Light Mode Accessibility**: Standardized light mode container backgrounds and styled text checkboxes (Bold, Italic, Underline) using native PyQt font helpers instead of hardcoded overrides, resolving unreadable white-on-white text issues.
