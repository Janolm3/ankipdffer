# Changelog

All notable changes to the **AnkiPdffer Dev** add-on will be documented in this file.

## [Unreleased]

### Changed
- Option tabs are centred with equal margins on both sides (and vertically). On the *Content* tab the line through the middle of the *Content* tab button is the left edge of the *Fields* box: the control column is sized for that, independently of the window size.

### Fixed
- Filter builder: the pop-up lists were narrower than their buttons on macOS, which elided entries (choosing *any* made *all* disappear).

## [1.4.3] - 2026-11-01

### Added
- **Filter builder**: the filter icon in the search field opens quick filters (card state, flag, the deck's tags, note type, added, reviewed, difficult cards) and *Build filter…* (⌘⇧F), a rule editor in the style of Mail rules: rows of *property – condition – value*, matching all or any of them, with the matching card count and the resulting Anki search shown live. Properties: card state, flag, tag, note type, card type, field, text, added, edited, reviewed (with the answer), first studied, due, interval, reviews, lapses, ease, FSRS difficulty / stability / retrievability, and any Anki search.
- **MathJax formulas are drawn**: `\(…\)` and `\[…\]` are rendered to vector SVG with the bundled MathJax 3.2.2 (Apache 2.0) before export, inline with the text and centred for display math — in PDFs, Preview and HTML. Formulas MathJax cannot read stay as written.
- **One box per card type**: note types whose card types show different fields (e.g. *Question 1/Answer 1* and *Question 2/Answer 2* with a shared *Context*) get one box per card, each with its own fields plus the shared ones. Detected from the card templates; the Fields tab shows which card a field belongs to and has a switch to override it. Plain *Basic (and reversed card)* stays one box per note.
- **Cloze colour**: revealed cloze answers and `[...]` gaps can use a colour of choice (red, orange, green, blue, purple, pink) instead of the theme colour, with lighter variants on dark pages.

### Changed
- Option tabs: the form is centred both horizontally and vertically in the tab at any window size, and pop-up menus and segmented controls share one width so their right edges line up.

### Fixed
- 1.4.2 could not open the export window once the PDF engine check had been saved (the status line was drawn before its buttons existed).

## [1.4.2] - 2026-11-01

### Added
- **Export to PDF button on the deck screen**: a native OS X–style button right below Anki's counts and *Study Now* (also on the "Congratulations" screen) opens AnkiPdffer on that deck. It can be hidden in Settings → *Deck screen*.
- **PDF engine setup on Windows**: *Settings → PDF engine → Set up…* now installs WeasyPrint on Windows too — Python (winget), Pango from MSYS2 (winget + pacman) and WeasyPrint 68.1 in a private environment inside the add-on's `user_files` folder (kept across updates), step by step with a live log. Without winget, the Python and MSYS2 download pages open and the remaining steps run afterwards. *Copy commands* gives the Windows commands.

### Changed
- The export window opens faster: the field table is built once instead of once per deck-picker change (reopening went from ~0.7 s to ~0.1 s on a 17,000-card collection).
- Settings → PDF engine is quieter: grey text with a coloured dot, the last result shows at once and is re-checked silently in the background ("Checking…" only appears after *Check again*).
- *Reset everything to defaults* looks like a normal button and turns muted red only on hover.
- The page footer of a PDF names the engine right after the version (*AnkiPdffer 1.4.2 · WeasyPrint · Fields · Compact · …*; *Qt WebEngine* for the built-in renderer).
- Option tabs: the right edges of the controls line up and the form's visual weight sits on the window's centre line instead of leaning right.

### Fixed
- The macOS-only bundled packages are no longer put in front of other Pythons, so a WeasyPrint installed for the system Python (Linux) or the private environment (Windows) can load. If another WeasyPrint version cannot run the layout pass, the PDF is rendered without it instead of falling back to the built-in renderer.

## [1.4.1] - 2026-11-01

### Changed
- **Preview PDF is the real PDF**: it is rendered with the same engine, settings and layout pass as *Export PDF* into a temporary file and opened, so what you preview is exactly what you get. (It used to be an HTML mock-up paginated by estimates.)
- **Smarter pagination**: after a first render, AnkiPdffer measures every page and lets a card continue on the next page only where that clearly saves space — never inside a field, never leaving a lone label or question, and never just to leave an empty frame. *Compact* fills pages (up to 12 % of a page may stay empty); *Standard* keeps cards whole unless a third of a page would be lost. On a 60-card test deck: compact 50 → 45 pages, standard 56 → 53 pages, with far less empty space and no mid-field cuts. The export log reports pages, split cards and empty space.
- **Loader stays in front**: progress is shown in a small floating panel above the export window (and Anki) until the job finishes, and the bar only moves forward.
- Deck and subdeck pickers are wider, show more entries, and their lists widen to fit long deck names.

### Added
- **PDF engine setup** in Settings: shows whether WeasyPrint is ready and opens a guide that checks Homebrew, Python 3.14 and Pango and installs what is missing with one click (or opens Terminal with the official Homebrew installer when Homebrew itself is missing).
- A subtle line in the page margin names what made the PDF: AnkiPdffer version, mode, layout and the note type(s) the cards come from, e.g. *AnkiPdffer 1.4.1 · Fields · Compact · Basic*.

### Fixed
- Links used the browser's default blue underline; they now match the theme.
- Images, tables and floated content could be clipped by field and card boxes; images are no longer cut and never split across pages.
- Long cards could split in the middle of a field, leave a field label alone at the bottom of a page, and lose their frame on one side of the split.
- *Strip Anki formatting* merged every line of a field into one paragraph; line breaks and list items are kept now.
- Collapsed `<details>` blocks (e.g. source notes) were hidden in the fallback renderer; they are exported open with a small caption.
- The System font fetched Google Fonts on every export; only the Inter font does now, so exports work offline.
- The search field's magnifier was blurry on Retina displays.
- The save dialog opened at the disk root (not writable); it now starts in the last export folder, or the Desktop.

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
