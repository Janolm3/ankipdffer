# AnkiPdffer

Export Anki decks to polished PDFs or standalone interactive HTML files.

AnkiPdffer turns flashcards into clean, readable documents for printing, offline study, sharing, and archiving.

[GitHub](https://github.com/Janolm3/ankipdffer)

---

## Highlights

- **Print-ready PDF export** with A4, A5, A3, Letter, custom sizes, margins, padding, and live preview.
- **Standalone HTML export** as a single offline file with embedded images.
- **Native Anki rendering** for Cloze, Image Occlusion, SVG masks, custom CSS, and complex templates.
- **Interactive image viewer** with zoom, pan, fullscreen preview, and keyboard support.
- **Clean customization** for themes, typography, spacing, borders, and layout density.
- **Subdeck tree picker** for browsing nested decks without digging through long lists.
- **No external dependencies** — runs directly inside Anki.

---

## Render Modes

### Fields Mode

Best for simple, uniform study sheets.

Map Anki fields to:

- Front
- Back
- Extra

Customize each field with labels, colors, alignment, and text styling.

> [!NOTE]
> Use **Fields Mode** when you want clean, consistent documents rather than exact Anki card rendering.

### Cards Mode

Best for Cloze, Image Occlusion, and complex templates.

Cards Mode renders cards using Anki’s native templates, preserving:

- Cloze deletions
- Image Occlusion masks
- SVG overlays
- Custom CSS
- Advanced card layouts

> [!TIP]
> Use **Cards Mode** for Image Occlusion cards to preserve SVG masks and occluded shapes.

---

## Export Options

### PDF

Create polished, print-ready documents with:

- Standard or custom page sizes
- Adjustable margins
- Card spacing and padding
- Compact layout options
- Live PDF preview before export

> [!TIP]
> Use **PDF Preview** before exporting to check natural page breaks and avoid awkward card splits.

### Standalone HTML

Generate a single portable HTML file with:

- Embedded images
- Offline access
- Interactive image viewing
- Optional grid layout
- Easy sharing across devices

> [!NOTE]
> Standalone HTML files work offline and keep images embedded, making them easy to share or archive.

---

## Usage

In Anki, open:

```text
Tools → Export Deck to PDF…
````

Then choose your deck, render mode, layout, theme, and export format.

Quick export current deck to Legacy HTML:

```text
Shift + P
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
* No external dependencies

---

## Source & License

AnkiPdffer is open source under the MIT License.

[github.com/Janolm3/ankipdffer](https://github.com/Janolm3/ankipdffer)
