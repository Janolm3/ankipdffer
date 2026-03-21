<div align="center">
  <h1>📄 AnkiPdffer</h1>
  <p><b>Export any Anki deck to a polished PDF or a standalone interactive HTML file — in seconds.</b></p>
  <p>
    <img src="https://img.shields.io/badge/Anki-23.11+-blue.svg" alt="Anki Version">
    <img src="https://img.shields.io/badge/Dependency-Zero-green.svg" alt="Zero Dependencies">
    <img src="https://img.shields.io/badge/License-MIT-purple.svg" alt="MIT License">
  </p>
</div>

---

## ✨ Features

AnkiPdffer transforms your flashcards into beautiful, readable documents for offline study, sharing, or archiving.

- **🖨️ PDF Export** — Print-ready output rendered via the built-in Chromium engine. Supports exact page sizes (A4, Letter, A3, A5) and customizable margins.
- **👁️ PDF Preview** — A paginated HTML preview so you can see exactly how the PDF will naturally break across pages *before* exporting.
- **🌐 Legacy HTML** — Generates a self-contained, single HTML file with embedded base64 images, a fully interactive image lightbox, and an optional grid layout mode.
- **🎨 Three Themes** — Choose from **Light ☀️**, **Dark 🌙**, or the sleek **Pro 🔵** theme.
- **🔤 Typography Control** — Pick from 12 font families and adjust both text size and line height.
- **📏 Layout & Sizing** — Select from Standard or Compact vertical layouts and quickly adjust card widths (Narrow, Medium, Wide, Full, Custom).
- **🗂️ Subdeck Tree Viewer** — Intelligently structured dropdown menus let you easily select nested subdecks (e.g., `Deck ↳ Subdeck ↳ Topic`).

### Two Powerful Render Engines
1. **Fields Mode**: Granular control. Assign each underlying card field to a specific position (Front, Back, Extra), and customize its appearance (Size, Background, Color, Alignment, Bold/Italic).
2. **Cards Mode (Cloze/Occlusion)**: Wysiwyg. Renders using Anki's native card templates. Perfect for Image Occlusion (SVG masks are preserved!) and complex cloze deletions.

---

## 🚀 Installation

### 📥 From AnkiWeb (Recommended)
1. Open Anki and navigate to **Tools → Add-ons → Get Add-ons**.
2. Enter the add-on code: `XXXXXXXX` *(Code available after AnkiWeb publish)*.
3. Restart Anki to apply changes.

### 📦 Manual Install
1. Download the latest `AnkiPdffer.zip` from the [Releases](../../releases) page.
2. In Anki, go to **Tools → Add-ons → Install from file…**.
3. Select the downloaded `.zip` file.
4. Restart Anki.

> **Requirements:** Anki **≥ 23.11**. (Qt6 strongly recommended, though Qt5/PyQt5 fallback is supported). No external dependencies.

---

## 🛠️ Usage

To get started, simply navigate to **Tools → Export Deck to PDF…** in the main Anki menu. 
*Pro-tip: Press **Shift+P** from the main view to instantly export the current deck as Legacy HTML.*

### ⚡ Basic Settings
| Setting | Description |
|---|---|
| **Theme** | Select Light, Dark, or Pro visual themes. |
| **Font & Size** | Choose from 12 bundled fonts and configure pixel size. |
| **Width** | Restrict column width: Narrow (520px), Medium (680px), Wide, Full, or Custom. |
| **Layout** | Toggle between Standard spacing or Compact to save real estate. |
| **Source** | Choose "Fields" for custom assembly or "Cards" for native formatting. |
| **Options** | Toggle Deck Title, Card Numbers, and Zebra Striping. |

### 🔧 Advanced Configuration
Control physical page properties. Define paper sizes (A4, A5, Letter, A3), page margins (in millimeters), card padding, and minimum inter-card gaps. Also allows stripping raw HTML inline styles or changing card border attributes (Rounded, Sharp, Double, None).

### 📋 Per-Field Settings (Fields Mode Only)
Map your Anki fields directly. Select whether a field belongs at the top (`Front`), bottom (`Back`), or as an appendix (`Extra`). Expand the **( ⋯ )** button to define exact background hues, alignment, and labels for specific fields.

### ⚙️ Persistent Settings
All your preferences can be saved, loaded, or reset from the Settings tab. They are stored safely in `settings.json`. AnkiPdffer also supports English and Polish UI languages natively!

---

## 🔍 Interactive Image Viewer (Legacy HTML)

Exported HTML files aren't just static! Click any image to launch a full-screen, native lightbox.

| Action | Result |
|---|---|
| **Scroll / Trackpad** | Zoom in/out smoothly. |
| **Click & Drag** | Pan freely around zoomed images. |
| **Double-Click** | Toggle instantly between 100% resolution and fit-to-screen. |
| **Escape / Click BG** | Dismiss the viewer. |

---

## 💡 Quick Tips

- **Image Occlusion Cards?** Make sure to set *Source* to *Cards (Cloze/Occlusion)* to accurately preserve SVG occlusion masks.
- **Mass Review?** Enable the **Grid Mode** checkbox at the bottom left before hitting Legacy HTML to arrange cards in a responsive Pinterest-style grid.
- **Paper Saving?** Use **Compact** Layout combined with **No border** Card Style for the highest density exports possible.

---

## 📝 License

Distributed under the **MIT License**. Free to use, modify, and distribute.
