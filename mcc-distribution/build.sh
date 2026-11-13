#!/usr/bin/env bash
# SPDX-License-Identifier: MPL-2.0
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)
git submodule update --init --depth=1
python3 mcc-distribution/prepare-branding.py
test -s mcc-distribution/branding/browser/branding.js
test -s mcc-distribution/branding/browser/branding.css
test -s mcc-distribution/branding/browser/images/toolbar-bg-logo.svg
PRODUCT=$(python3 -c 'import json; print(json.load(open("mcc-distribution/distribution.json"))["product"])')
VENDOR=$(python3 -c 'import json; print(json.load(open("mcc-distribution/distribution.json"))["vendor"])')
mkdir -p mcc-distribution/branding/engine
for NAME in about logo logo_inverted logo-sc logo-sc_inverted; do
  cp mcc-distribution/branding/office.svg "mcc-distribution/branding/engine/$NAME.svg"
done
rsvg-convert -w 800 -h 400 mcc-distribution/branding/office.svg -o mcc-distribution/branding/engine/intro.png
rsvg-convert -w 1600 -h 800 mcc-distribution/branding/office.svg -o mcc-distribution/branding/engine/intro-highres.png
rsvg-convert -w 128 -h 128 mcc-distribution/branding/office.svg -o mcc-distribution/branding/favicon.png
python3 - <<'PY'
from pathlib import Path
import struct
p=Path('mcc-distribution/branding')
png=(p/'favicon.png').read_bytes()
(p/'favicon.ico').write_bytes(struct.pack('<HHH',0,1,1)+struct.pack('<BBBBHHII',128,128,0,0,1,32,len(png),22)+png)
PY
cd engine
./autogen.sh --with-distro=CPLinux-LOKit --disable-epm --without-package-format \
  --disable-symbols --with-parallelism=4 "--with-product-name=$PRODUCT" \
  "--with-vendor=$VENDOR" "--with-branding=$ROOT/mcc-distribution/branding/engine"
make -j4
cd "$ROOT"
./autogen.sh
./configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var \
  --disable-tests --disable-debug --disable-branding --enable-bundle \
  "--with-lokit-path=$ROOT/engine/include" --with-lo-path=/opt/collaboraoffice \
  "--with-vendor=$VENDOR" "--with-app-name=$PRODUCT" \
  "--with-app-branding=$ROOT/mcc-distribution/branding/browser"
make -j4
mkdir -p mcc-distribution/instdir/opt
cp -a engine/instdir mcc-distribution/instdir/opt/collaboraoffice
python3 mcc-distribution/patch-translations.py \
  --input-root mcc-distribution/instdir/opt/collaboraoffice/program/resource \
  --output-root mcc-distribution/instdir/opt/collaboraoffice/program/resource \
  --manifest translation-manifest.json
make DESTDIR="$ROOT/mcc-distribution/instdir" install
python3 mcc-distribution/patch-welcome.py \
  --input-root mcc-distribution/instdir/usr/share/coolwsd/browser/dist/l10n \
  --output-root mcc-distribution/instdir/usr/share/coolwsd/browser/dist/l10n \
  --manifest welcome-manifest.json
find mcc-distribution/instdir/usr/share/coolwsd -name favicon.ico -type f -exec cp mcc-distribution/branding/favicon.ico {} \;
mkdir -p mcc-distribution/instdir/usr/share/coolwsd/browser/dist/licenses
cp COPYING mcc-distribution/instdir/usr/share/coolwsd/browser/dist/licenses/COPYING.txt
cp THIRDPARTYLICENSES mcc-distribution/instdir/usr/share/coolwsd/browser/dist/licenses/THIRDPARTYLICENSES.txt
cp browser/LICENSE mcc-distribution/instdir/usr/share/coolwsd/browser/dist/licenses/BROWSER-LICENSE.txt
cp engine/instdir/LICENSE mcc-distribution/instdir/usr/share/coolwsd/browser/dist/licenses/ENGINE-LICENSE.txt
cp mcc-distribution/LICENSE-MPL-2.0.txt mcc-distribution/instdir/usr/share/coolwsd/browser/dist/licenses/
cp mcc-distribution/licenses.html mcc-distribution/instdir/usr/share/coolwsd/browser/dist/licenses.html
docker build --label "org.opencontainers.image.source=$(git remote get-url origin)" \
  --label "org.opencontainers.image.revision=$(git rev-parse HEAD)" \
  --label "org.opencontainers.image.version=$(python3 -c 'import json; print(json.load(open("mcc-distribution/distribution.json"))["release"])')" \
  -t gestionpyme-office:build -f mcc-distribution/Dockerfile mcc-distribution
