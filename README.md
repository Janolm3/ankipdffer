# AnkiPdffer

Export Anki decks to polished PDFs or standalone interactive HTML files.

AnkiPdffer turns flashcards into clean, readable documents for printing, offline study, sharing, and archiving.

<p align="center">
  <img src="docs/screenshots/window-content.png" width="49%" alt="AnkiPdffer export window, Content tab">
  <img src="docs/screenshots/window-dark.png" width="49%" alt="AnkiPdffer export window in dark mode">
</p>

---

## What's new in 1.4.1

- **Preview = the real PDF**, rendered exactly like the export.
- **Smarter pagination**: cards continue on the next page only where it clearly saves space, never inside a field — compact exports have far less empty space.
- **Clean links, uncropped images**, line breaks kept when stripping formatting.
- **PDF engine setup** in Settings with one-click install, and a loader that stays in front.

## What's new in 1.4.0

- **Worksheets**: questions with an answer key, or a question page followed by its answer page.
- **Image Occlusion pages**: one page with every mask hidden, the next with them revealed.
- **Cloze modes**: hide answers as `[...]`, reveal them, or show both one after the other.
- **Note type editor and field presets**: the Fields tab opens on the type of the card you are studying.
- **Redesigned, responsive Mac-style window** with automatic saving, presets and 10 interface languages.

Full list in the [CHANGELOG](CHANGELOG.md).

---

## Highlights

- **Print-ready PDF export** with A4, A5, A3, Letter, custom sizes, margins, padding, page numbers, and live preview.
- **Worksheet layouts**: questions and answers together, all questions followed by an answer key, or a question page followed by its answer page.
- **Image Occlusion pages**: one page with every mask covering the image, the next with the masks removed.
- **Cloze modes**: reveal, hide as `[...]`, hidden-then-revealed, or Anki's native card-per-cloze.
- **Per-note-type field settings** with field presets, automatic saving, option presets, and a one-click reset.
- **Filter, order and count**: any Anki search, deck / creation / shuffled order, and a live card count.
- **Standalone HTML export** as a single offline file with embedded images.
- **Interface in 10 languages**: English, Polski, Español, Português, Deutsch, Français, Italiano, Русский, 中文, 日本語.
- **Lightweight Mac-style window** (light and dark) that adapts to its size. Opening the add-on again restores the same window.

---

## The Window

Pick the deck, subdeck and an optional filter at the top; the footer shows how many cards and notes will be exported. Options are grouped in five tabs:

| Tab | What it sets |
| --- | --- |
| **Content** | Source (fields or rendered cards), question / answer layout, cloze, Image Occlusion, order, title and numbers |
| **Appearance** | Theme, font and size, card width, layout density, card style, zebra / high-contrast / grid options |
| **Page** | Paper size, margins, padding, spacing, line height, image height, page numbers |
| **Fields** | Which field goes where and how it looks, per note type (Fields source only) |
| **Settings** | Option presets, language, PDF engine setup, debug log, reset |

Everything is saved as you go — there is no *Save* button.

---

## Render Modes

### Fields Mode

Best for simple, uniform study sheets.

<p align="center">
  <img src="docs/screenshots/window-fields.png" width="70%" alt="Fields tab: one row per field with section, size, style and label">
</p>

Map Anki fields to:

- Front
- Back
- Extra

Customize each field with labels, size, bold / italic / underline, colors, background, and alignment (*⋯* opens the extra options). Untick a field to leave it out.

The Fields tab edits **one note type at a time**. It opens on the type of the card you are studying (or the deck's most used type), and the *Note type* pop-up switches to any other type in your collection. Settings are stored per note type; *Reset* restores a type's defaults.

**Presets** (next to the note type) save how a note type's fields look and apply it to any other type — fields are matched by name, then by position.

In Fields mode, a note is exported once even if it generates several cards. Cloze fields follow the **Cloze** option and Image Occlusion notes are drawn from their mask data.

### Cards Mode

Best for complex templates and for printing the front and back of each card as Anki renders them.

Cards Mode renders cards using Anki's native templates, preserving custom CSS and advanced card layouts. Sounds and Anki's interactive Image Occlusion canvas are replaced by static output.

---

## Question / Answer Layout

| Option | Result |
| --- | --- |
| Together on one card | Question and answer in the same block (default) |
| All questions, then answers | Every question first, then an answer key |
| Question page, then answer page | Each card's question on one page and its answer on the next |

## Cloze

| Option | Result |
| --- | --- |
| Reveal (highlighted) | Answers shown and highlighted |
| Hide answers `[...]` | Answers replaced by `[...]` (or the hint, `[hint]`) |
| Hidden, then revealed | The hidden version followed by the revealed one |
| Like Anki | One card per cloze number, as in Anki |

Combine *Hide answers* with *All questions, then answers* to get a printable cloze worksheet with an answer key.

## Image Occlusion

Anki's Image Occlusion notes (rectangles, ellipses, polygons) are drawn directly by the exporter:

<p align="center">
  <img src="docs/screenshots/pdf-occlusion-hidden.png" width="40%" alt="Image Occlusion page with all masks hidden">
  <img src="docs/screenshots/pdf-occlusion-revealed.png" width="40%" alt="The same image with the masks revealed and numbered">
</p>

- **All masks at once**: one entry per note — the image with every mask on top, then (with a question / answer layout) the same image with the masks removed and numbered outlines.
- **One card per mask**: one entry per mask, as Anki schedules them.

---

## Export Options

### PDF

Create polished, print-ready documents with:

- Standard or custom page sizes
- Adjustable margins
- Card spacing and padding
- Compact layout options
- Optional page numbers (`3 / 12`)
- Live PDF preview before export

> [!TIP]
> Use **Preview PDF** before exporting to check natural page breaks and avoid awkward card splits.

### Standalone HTML

Generate a single portable HTML file with:

- Embedded images
- Offline access
- Interactive image viewing
- Optional grid layout
- Easy sharing across devices

---

## Settings and Presets

- **Option presets** (Settings tab): store all current options and field settings under a name, apply or delete them later.
- **Field presets** (Fields tab): store only how one note type's fields look, and reuse it on other note types.
- **Reset everything to defaults** restores the original options and field settings (your language and presets are kept).
- **Language** switches the interface immediately.

Settings live in `settings.json` inside the add-on folder.

---

## Usage

In Anki, open:

```text
Tools → AnkiPdffer → Open export dialog…
```

Then choose your deck (and optional filter), adjust the tabs, and export.

Or open a deck and click **Export to PDF** below *Study Now* — the window opens on that deck (Settings → *Deck screen* hides the button).

Quick export of the current deck to Legacy HTML:

```text
Shift + Alt + P
```

### Keyboard Shortcuts

In the export window:

| Shortcut | Action |
| --- | --- |
| ⌘1 – ⌘5 | Switch tabs |
| ⌘F | Filter cards |
| ⌘P | Preview PDF |
| ⌘↩ | Export PDF |
| ⌘W | Close |

(Ctrl instead of ⌘ on Windows / Linux.)

---

## Image Viewer

Click any image in the exported HTML to open it fullscreen.

* Scroll to zoom
* Drag to pan
* Double-click to toggle 100%
* Press Escape to close

---

## Tips

> [!TIP]
> For dense review sheets, enable **Appearance → Grid layout (HTML)** and use **Layout: Compact** with **Card style: No border**.

> [!TIP]
> For paper-saving exports, reduce padding and spacing on the **Page** tab and switch to a compact layout.

> [!TIP]
> For self-testing, combine **Cloze: Hide answers** with **Q / A: Question page, then answer page**.

---

## Requirements

* Anki 23.11+
* PDF export uses the bundled WeasyPrint in an isolated Python process. On macOS this needs **Python 3.14** and **Pango** — **Settings → PDF engine → Set up…** checks them and installs what is missing with one click (or run `brew install python@3.14 pango`). On Windows the same button installs Python, Pango (MSYS2) and WeasyPrint into the add-on's `user_files` folder (winget is used when available). If they are not found, AnkiPdffer falls back to Qt WebEngine's PDF renderer (works everywhere, with simpler pagination). HTML export has no extra requirements.

---

## Development

```bash
dev/dev.sh check         # headless regression checks (real add-on code, temporary collection)
dev/dev.sh preview       # dialog screenshots + sample PDFs -> dev/out/index.html
dev/dev.sh sandbox       # throw-away Anki profile with a sample deck and this add-on
dev/dev.sh sandbox-stop  # quit only the sandbox Anki
dev/dev.sh sync          # copy the working tree into your Anki add-ons folder
./release.sh 1.4.0 --build-only   # dist/AnkiPdffer-1.4.0.ankiaddon (+ .zip), nothing published
```

New interface languages go into `translations.py`; missing strings fall back to English. The AnkiWeb description lives in [`docs/ANKIWEB.md`](docs/ANKIWEB.md).

---

## Source & License

AnkiPdffer is open source under the MIT License.

[github.com/Janolm3/ankipdffer](https://github.com/Janolm3/ankipdffer) · [AnkiWeb](https://ankiweb.net/shared/info/1987190048)
