#!/usr/bin/env bash
# Usage: ./release.sh [version]
# Example: ./release.sh 1.0.1
# Builds AnkiPdffer.zip and creates a GitHub release via gh CLI.

set -e

VERSION="${1:-1.0.0}"
ADDON_DIR="$(cd "$(dirname "$0")" && pwd)"
PACKAGE_NAME="AnkiPdffer"
ZIP_NAME="${PACKAGE_NAME}-${VERSION}.zip"
DIST_DIR="${ADDON_DIR}/dist"

echo "==> Building ${ZIP_NAME}"
mkdir -p "${DIST_DIR}"

# Build the zip — Anki expects __init__.py + manifest.json at the root of the zip
cd "${ADDON_DIR}"

echo "==> Pruning unneeded files from .vendor/ to reduce package size"
find .vendor -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find .vendor -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find .vendor -type f -name "*.c" -delete 2>/dev/null || true
find .vendor/pyphen/dictionaries -type f ! -name "*en*" ! -name "*pl*" ! -name "*README*" -delete 2>/dev/null || true

zip -r "${DIST_DIR}/${ZIP_NAME}" \
    __init__.py \
    manifest.json \
    .vendor/ \
    -x "*.pyc" -x "*/__pycache__/*" -x "*.DS_Store" -x "settings.json" -x "dist/*"

echo "==> Created ${DIST_DIR}/${ZIP_NAME}"

# Update version in manifest.json
if command -v jq &>/dev/null; then
    tmp=$(mktemp)
    jq --arg v "${VERSION}" '.human_version = $v' manifest.json > "$tmp" && mv "$tmp" manifest.json
    echo "==> manifest.json updated to ${VERSION}"
fi

# GitHub release (requires gh CLI: https://cli.github.com/)
if ! command -v gh &>/dev/null; then
    echo "==> gh CLI not found — skipping GitHub release."
    echo "    Install from: https://cli.github.com/"
    exit 0
fi

echo "==> Creating GitHub release v${VERSION}"
gh release create "v${VERSION}" \
    "${DIST_DIR}/${ZIP_NAME}" \
    --title "v${VERSION}" \
    --notes "$(cat <<EOF
## AnkiPdffer v${VERSION}

### Install
1. Download \`${ZIP_NAME}\` below
2. Anki → Tools → Add-ons → Install from file…
3. Restart Anki

See [README](README.md) for full documentation.
EOF
)"

echo "==> Release v${VERSION} published."
