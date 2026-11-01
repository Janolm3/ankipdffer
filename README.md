# AnkiPdffer

Export Anki decks to polished PDFs or standalone interactive HTML files.

AnkiPdffer turns flashcards into clean, readable documents for printing, offline study, sharing, and archiving.

---

## Highlights

- **Print-ready PDF export** with A4, A5, A3, Letter, custom sizes, margins, padding, page numbers, and live preview.
- **Worksheet layouts**: questions and answers together, all questions followed by an answer key, or a question page followed by its answer page.
- **Image Occlusion pages**: one page with every mask covering the image, the next with the masks removed.
- **Cloze modes**: reveal, hide as `[...]`, hidden-then-revealed, or Anki's native card-per-cloze.
- **Per-note-type settings**, automatic saving, named presets, and a one-click reset.
- **Filter, order and count**: any Anki search, deck / creation / shuffled order, and a live card count.
- **Standalone HTML export** as a single offline file with embedded images.
- **Interface in 10 languages**: English, Polski, Español, Português, Deutsch, Français, Italiano, Русский, 中文, 日本語.
- **One window**: opening the add-on again restores the existing window instead of creating a new one.

---

## Render Modes

### Fields Mode

Best for simple, uniform study sheets.

Map Anki fields to:

- Front
- Back
- Extra

Customize each field with labels, colors, alignment, and text styling. Field settings are stored **per note type**, so Basic, Cloze and Image Occlusion notes each keep their own look (use *Reset* in a note type's header to restore its defaults).

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

Anki's new Image Occlusion notes (rectangles, ellipses, polygons) are drawn directly by the exporter:

- **All masks at once**: one entry per note — the image with every mask on top, then (with a question/answer layout) the same image with the masks removed and numbered outlines.
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

## Settings

Everything you change is saved automatically — there is no *Save* button, and nothing is lost when you close the window or switch decks. The **Settings** tab also offers:

- **Presets**: store the current options and field settings under a name, apply or delete them later.
- **Reset everything to defaults**: restores the original options and field settings (your language and presets are kept).
- **Language**: switch the interface language; the window rebuilds immediately.

Settings live in `settings.json` inside the add-on folder.

---

## Usage

In Anki, open:

```text
Tools → AnkiPdffer → Open export dialog…
```

Then choose your deck (and optional filter), render mode, layout, theme, and export format.

Quick export of the current deck to Legacy HTML:

```text
Shift + Alt + P
```

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
> For dense review sheets, enable **Grid Mode** and use **Compact Layout + No Border**.

> [!TIP]
> For paper-saving exports, reduce spacing and switch to a compact card layout.

---

## Requirements

* Anki 23.11+
* PDF export uses the bundled WeasyPrint in an isolated Python process. On macOS this needs **Python 3.14** and **Pango** (`brew install python@3.14 pango`). If they are not found, AnkiPdffer falls back to Qt WebEngine's PDF renderer (works everywhere, with simpler pagination). HTML export has no extra requirements.

---

## Development

```bash
dev/dev.sh check      # headless regression checks (real add-on code, temporary collection)
dev/dev.sh preview    # dialog screenshots + sample PDFs -> dev/out/index.html
dev/dev.sh sandbox    # throw-away Anki profile with a sample deck and this add-on
dev/dev.sh sync       # copy the working tree into your Anki add-ons folder
```

New interface languages go into `translations.py`; missing strings fall back to English.

---

## Source & License

AnkiPdffer is open source under the MIT License.

[github.com/Janolm3/ankipdffer](https://github.com/Janolm3/ankipdffer)
