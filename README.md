# AnkiPdffer

Export Anki decks to clean PDFs or standalone interactive HTML files.

AnkiPdffer turns flashcards into readable documents for printing, offline study, sharing, and archiving.

[GitHub](https://github.com/Janolm3/ankipdffer)

---

## Features

- **PDF export** — print-ready PDFs with A4, A5, A3, Letter, custom sizes, margins, padding, and live preview.
- **Standalone HTML** — one offline HTML file with embedded images.
- **Themes** — Light, Dark, and Pro.
- **Typography** — 12 fonts, adjustable text size, and line height.
- **Layouts** — compact mode, grid view, custom widths, borders, spacing, and padding.
- **Subdeck picker** — browse nested decks in a clean tree view.
- **Progress loader** — animated export overlay with progress updates.

---

## Render Modes

### Fields Mode

Best for simple, clean study sheets.

Map Anki fields to:

- Front
- Back
- Extra

Customize each field with colors, alignment, labels, and text styling.

### Cards Mode

Best for Cloze, Image Occlusion, and complex templates.

Renders cards using Anki’s native templates and preserves CSS, SVG masks, cloze styling, and custom layouts.

---

## Usage

In Anki, open:

```text
Tools → Export Deck to PDF…
````

Then choose your deck, layout, theme, and export format.

Quick export current deck to Legacy HTML:

```text
Shift + P
```

---

## HTML Image Viewer

Click any image in the exported HTML to open it fullscreen.

* Scroll to zoom
* Drag to pan
* Double-click to toggle 100%
* Press Escape to close

---

## Tips

* Use **Cards Mode** for Image Occlusion.
* Use **Grid Mode** for dense review sheets.
* Use **Compact Layout + No Border** to save paper.

---

## Requirements

* Anki 23.11+
* No external dependencies

---

## Source & License

Open source under the MIT License.

[github.com/Janolm3/ankipdffer](https://github.com/Janolm3/ankipdffer)
