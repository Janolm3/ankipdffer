Export Anki decks to clean PDFs or standalone interactive HTML files.

AnkiPdffer turns flashcards into readable documents for printing, offline study, sharing, and archiving.

Open source on GitHub (screenshots, full documentation, changelog):

[github.com/Janolm3/ankipdffer](https://github.com/Janolm3/ankipdffer)

[Buy Me a Coffee](https://buymeacoffee.com/janolm)

## New in 1.4.1

- **Preview PDF is the real PDF** — exactly what Export produces.
- **Smarter pagination** — cards continue on the next page only where it clearly saves space, never in the middle of a field. Compact exports have far less empty space.
- **Clean links and uncropped images**; *Strip Anki formatting* keeps line breaks.
- **PDF engine setup** in Settings — checks and installs what WeasyPrint needs with one click.
- The progress panel stays in front until the export is done.

## New in 1.4.0

- **Worksheets** — print all questions followed by an answer key, or each question on one page and its answer on the next.
- **Image Occlusion pages** — one page with every mask hidden, the next with the masks revealed and numbered. Choose all masks at once or one card per mask.
- **Cloze modes** — hide answers as `[...]` (or `[hint]`), reveal them, show the hidden version followed by the revealed one, or keep Anki's card-per-cloze.
- **Note type editor** — the Fields tab opens on the type of the card you are studying; any note type can be edited, and each keeps its own settings.
- **Field presets** — save how a note type's fields look and apply it to any other type.
- **Redesigned window** — clean Mac-style look in light and dark mode, adapts to any window size, keyboard shortcuts.
- **Settings saved automatically**, option presets, reset to defaults, and the same window is reused instead of opening new ones.
- **10 interface languages** — English, Polski, Español, Português, Deutsch, Français, Italiano, Русский, 中文, 日本語.
- **Filter, order and count** — any Anki search (e.g. `tag:leech is:due`), deck / creation / shuffled order, live card count, page numbers.

## Features

- **PDF export** — print-ready PDFs with A4, A5, A3, Letter, custom margins, page numbers, and PDF preview.
- **Standalone HTML** — single offline HTML file with embedded images and an interactive image viewer.
- **Themes** — Light, Dark, and Pro.
- **Typography** — 12 font families, adjustable text size, and line height.
- **Layout control** — compact mode, custom card widths, spacing, padding, and borders.

## Render Modes

### Fields Mode

Best for simple, clean exports and worksheets.

Map each Anki field to Front, Back, or Extra and set its size, bold / italic / underline, label, colors, background, and alignment. Settings are remembered per note type.

### Cards Mode

Best for complex card templates.

Renders cards using Anki's native templates and preserves custom CSS and layouts. Image Occlusion masks and cloze deletions are drawn statically, so they print correctly.

## Usage

In Anki, open:

```
Tools → AnkiPdffer → Open export dialog…
```

Pick the deck, adjust the tabs (Content, Appearance, Page, Fields, Settings), then Preview PDF or Export PDF.

Or open a deck and click **Export to PDF** below *Study Now*.

Quick export of the current deck to Legacy HTML:

```
Shift + Alt + P
```

Shortcuts in the export window: Cmd/Ctrl+1–5 tabs, Cmd/Ctrl+F filter, Cmd/Ctrl+P preview, Cmd/Ctrl+Return export.

## HTML Image Viewer

Click any image in the exported HTML to open it fullscreen.

- Scroll to zoom
- Drag to pan
- Double-click to toggle 100%
- Press Escape to close

## Tips

- For a cloze worksheet, set **Cloze: Hide answers** and **Q / A: All questions, then answers**.
- For self-testing with Image Occlusion, use **Q / A: Question page, then answer page**.
- For dense review sheets, use **Layout: Compact**, **Card style: No border**, and **Grid layout (HTML)**.

## Requirements

- Anki 23.11+
- PDF export uses the bundled WeasyPrint. On macOS it needs Python 3.14 and Pango — Settings → PDF engine → Set up… installs them with one click. Without them AnkiPdffer falls back to Anki's built-in PDF renderer. HTML export has no extra requirements.
