# Changelog

All notable changes to the **AnkiPdffer Dev** add-on will be documented in this file.

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
