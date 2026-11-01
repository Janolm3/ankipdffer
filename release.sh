#!/usr/bin/env bash
# Usage: ./release.sh [version] [--build-only]
# Example: ./release.sh 1.4.0 --build-only
#
# Builds dist/AnkiPdffer-<version>.zip from a clean staging copy (the working tree is not
# pruned or modified except for manifest.json's human_version) and, unless --build-only
# is given, publishes it as a GitHub release via the gh CLI.
# The version defaults to the one already in manifest.json.

set -euo pipefail

ADDON_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "${ADDON_DIR}"

BUILD_ONLY=0
VERSION=""
for arg in "$@"; do
    case "${arg}" in
        --build-only) BUILD_ONLY=1 ;;
        -*) echo "unknown option: ${arg}" >&2; exit 1 ;;
        *) VERSION="${arg}" ;;
    esac
done
if [ -z "${VERSION}" ]; then
    VERSION="$(python3 -c "import json;print(json.load(open('manifest.json'))['human_version'])")"
fi

PACKAGE_NAME="AnkiPdffer"
ZIP_NAME="${PACKAGE_NAME}-${VERSION}.zip"
DIST_DIR="${ADDON_DIR}/dist"

# Keep every version string in step with the release version.
echo "==> Setting version ${VERSION}"
python3 - "${VERSION}" <<'PY'
import json, re, sys
version = sys.argv[1]

with open("manifest.json", encoding="utf-8") as fh:
    manifest = json.load(fh)
manifest["human_version"] = version
with open("manifest.json", "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, indent=2)
    fh.write("\n")

with open("__init__.py", encoding="utf-8") as fh:
    src = fh.read()
src = re.sub(r'(def _addon_version\(default=")[^"]*(")', r"\g<1>" + version + r"\g<2>", src)
src = re.sub(r'(EXPORT_BUILD = ")[^"-]*(-)', r"\g<1>" + version + r"\g<2>", src)
with open("__init__.py", "w", encoding="utf-8") as fh:
    fh.write(src)
PY

echo "==> Building ${ZIP_NAME}"
mkdir -p "${DIST_DIR}"
STAGE="$(mktemp -d)"
trap 'rm -rf "${STAGE}"' EXIT

# Anki expects __init__.py + manifest.json at the root of the zip.
# Every top-level module is shipped (store.py, translations.py, ...); dev tooling,
# user data and build output are not.
rsync -a \
    --exclude ".git" --exclude ".gitignore" --exclude "dev/" --exclude "dist/" \
    --exclude "__pycache__/" --exclude "*.pyc" --exclude ".DS_Store" \
    --exclude "settings.json" --exclude "meta.json" --exclude "last_export_log.txt" \
    --exclude "release.sh" --exclude "CHANGELOG.md" --exclude "README.md" \
    ./ "${STAGE}/"

echo "==> Pruning unneeded files from .vendor/ to reduce package size"
find "${STAGE}/.vendor" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find "${STAGE}/.vendor" -type d -name "*.dist-info" -prune -exec rm -rf {} + 2>/dev/null || true
find "${STAGE}/.vendor" -type f -name "*.c" -delete 2>/dev/null || true
find "${STAGE}/.vendor/pyphen/dictionaries" -type f ! -name "*en*" ! -name "*pl*" ! -name "*README*" -delete 2>/dev/null || true

rm -f "${DIST_DIR}/${ZIP_NAME}"
(cd "${STAGE}" && zip -qr "${DIST_DIR}/${ZIP_NAME}" . -x "*.pyc" -x "*/__pycache__/*" -x "*.DS_Store")

# Sanity: the modules __init__.py imports must be in the zip.
LISTING="$(unzip -l "${DIST_DIR}/${ZIP_NAME}")"
for required in __init__.py manifest.json store.py translations.py; do
    grep -q " ${required}\$" <<<"${LISTING}" || {
        echo "!! ${required} missing from ${ZIP_NAME}" >&2
        exit 1
    }
done
echo "==> Created ${DIST_DIR}/${ZIP_NAME} ($(du -h "${DIST_DIR}/${ZIP_NAME}" | cut -f1))"

if [ "${BUILD_ONLY}" = "1" ]; then
    echo "==> --build-only: not publishing."
    exit 0
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

See [README](README.md) and [CHANGELOG](CHANGELOG.md) for details.
EOF
)"

echo "==> Release v${VERSION} published."
