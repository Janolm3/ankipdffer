# AnkiPdffer 🖨️

Export Anki decks to clean, print-ready PDFs or standalone interactive HTML files. 

AnkiPdffer transforms your flashcards into beautiful, readable documents optimized for printing, offline study, easy sharing, and archival.

[![GitHub License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](https://github.com/Janolm3/ankipdffer)
[![Anki Version Compatibility](https://img.shields.io/badge/Anki-23.11+-blue?style=flat-square)](https://apps.ankiweb.net/)

---

## ✨ Features

- 📄 **PDF Export** — Generate print-ready PDFs with standard page sizes (`A4`, `A5`, `A3`, `Letter`) or custom dimensions. Supports adjustable margins, padding, and an interactive live PDF preview.
- 🌐 **Standalone HTML** — Export your deck as a single, self-contained offline HTML file with embedded images (Base64), perfect for studying or sharing on any device.
- 🎨 **Modern Themes** — Choose between **Light** (clean Slate), **Dark** (night mode Slate), and **Pro** (electric blue accents) color schemes designed for readability.
- ✍️ **Typography Control** — Pick from 12 font families (including system defaults, Inter, Helvetica, Arial, Georgia, Palatino, Fira Code, and more), adjust text sizes, and customize line heights.
- 📐 **Layout Customization** — Support for compact mode, grid views, custom card widths, zebra striping, adjustable borders, padding, and min-gap spacing.
- 🗂️ **Nested Deck Selection** — Easily browse and select subdecks using an intuitive, clean tree-view picker.
- 🔄 **Determinate Loader** — Features a modern animated loader overlay during export with progress-tracking and state updates.

---

## 🛠️ Render Modes

AnkiPdffer offers two distinct rendering engines depending on your cards' complexity:

### 📋 Fields Mode
*Best for simple, clean, and uniform study sheets.*
- Map each Anki field to **Front**, **Back**, or **Extra** sections.
- Customize styling for each field independently (background color, text color, alignment, labels, and bold/italic/underline overrides).

### 🃏 Cards Mode
*Best for Cloze deletions, Image Occlusion, and custom card templates.*
- Renders cards using Anki's native templates and styles.
- Preserves custom CSS, SVG masks, Cloze deletion styling, and advanced card layouts exactly as they appear in Anki.

---

## 🚀 Usage

### Standard Export
1. In Anki, open the menu: **Tools** → **Export Deck to PDF…**
2. Configure your layout, theme, fields, or templates in the dialog.
3. Click **Preview PDF** to check the output, or click **Export PDF** / **Legacy HTML** to save the file.

### Quick Export
- Press **Shift + P** to instantly export the currently selected deck using the Legacy HTML renderer.

---

## 🔍 Interactive HTML Image Viewer

All images in the exported standalone HTML files feature an embedded interactive viewer. Simply **click any image** to open it fullscreen:
- 🖱️ **Scroll** to zoom in and out
- 🤚 **Drag** to pan around the zoomed image
- ⚡ **Double-click** to toggle between 100% and fit-to-screen
- ❌ Press **Escape** or click the close button to exit

---

## 💡 Pro Tips

> [!TIP]
> **For Image Occlusion:** Always use **Cards Mode** to preserve the SVG masks and occluded shapes.

> [!TIP]
> **For Dense Review Sheets:** Enable **Grid Mode** and choose a **Compact Layout + No Border** style to maximize space and save paper.

---

## ⚙️ Requirements

* **Anki 23.11+**
* **No external dependencies** (uses Anki's built-in QtWebEngine)

---

## 🔗 Source & License

AnkiPdffer is open source under the MIT License. Contributions and feedback are welcome!

GitHub Repository: [github.com/Janolm3/ankipdffer](https://github.com/Janolm3/ankipdffer)
