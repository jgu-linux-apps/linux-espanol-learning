#!/bin/sh
# Buduje pakiet .deb: ./build-deb.sh  ->  dist/linux-espanol-learning_<wersja>_all.deb
set -e
cd "$(dirname "$0")"
VER=$(sed -n 's/^VERSION = "\(.*\)"/\1/p' src/espanol/__init__.py)
PKG=linux-espanol-learning
ROOT=build/${PKG}_${VER}_all
rm -rf build && mkdir -p "$ROOT/DEBIAN" dist
SHARE=$ROOT/usr/share/$PKG
mkdir -p "$SHARE" "$ROOT/usr/bin" "$ROOT/usr/share/applications" "$ROOT/usr/share/doc/$PKG"
cp -r src/espanol "$SHARE/"
cp -r data "$SHARE/"
find "$SHARE" -name "__pycache__" -type d -prune -exec rm -rf {} +
install -m 755 bin/$PKG "$ROOT/usr/bin/$PKG"
install -m 644 packaging/io.github.jgu.EspanolLearning.desktop "$ROOT/usr/share/applications/"
for v in "" "-dark"; do
  install -D -m 644 icons/$PKG$v.svg "$ROOT/usr/share/icons/hicolor/scalable/apps/$PKG$v.svg"
  for s in 48 64 128 256; do
    mkdir -p "$ROOT/usr/share/icons/hicolor/${s}x${s}/apps"
    rsvg-convert -w $s -h $s icons/$PKG$v.svg -o "$ROOT/usr/share/icons/hicolor/${s}x${s}/apps/$PKG$v.png"
  done
done
# icon follows light/dark also while the app is closed (session autostart helper, also started by the app)
install -D -m 755 packaging/icon-watch.sh "$ROOT/usr/lib/$PKG/icon-watch.sh"
install -D -m 644 packaging/$PKG-icon.desktop "$ROOT/etc/xdg/autostart/$PKG-icon.desktop"
install -m 644 README.md "$ROOT/usr/share/doc/$PKG/README.md"
install -m 644 LICENSE "$ROOT/usr/share/doc/$PKG/copyright"
install -m 755 packaging/postinst packaging/postrm "$ROOT/DEBIAN/"
SIZE=$(du -sk "$ROOT/usr" "$ROOT/etc" | awk '{s+=$1} END {print s}')
sed "s/@SIZE@/$SIZE/; s/^Version: .*/Version: $VER/" packaging/control > "$ROOT/DEBIAN/control"
find "$ROOT" -type d -exec chmod 755 {} +
find "$ROOT/usr/share" -type f -exec chmod 644 {} +
dpkg-deb --root-owner-group --build "$ROOT" "dist/${PKG}_${VER}_all.deb"
echo "Gotowe: dist/${PKG}_${VER}_all.deb"
