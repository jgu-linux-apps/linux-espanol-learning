#!/bin/sh
# Linux Español Learning: small background helper that keeps the app icon (dock, app menu) in step with the
# system light/dark theme, also while the app is closed. It does nothing else and does not start the app.
# Dark: the dark icons (SVG + PNG sizes) are copied to ~/.local/share/icons/hicolor (wins over /usr/share).
# Light: the copies are removed, so the light icons of the package are used.
ID=linux-espanol-learning
SRC=/usr/share/icons/hicolor
[ -f "$SRC/scalable/apps/$ID-dark.svg" ] || exit 0
# one helper per user session (the app also starts it)
LOCK="${XDG_RUNTIME_DIR:-/tmp}/$ID-icon.lock"
exec 9>"$LOCK" && flock -n 9 || exit 0
BASE="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"
SIZES="48 64 128 256"

is_dark() {
    case "$(gsettings get org.gnome.desktop.interface color-scheme 2>/dev/null)" in *dark*) return 0 ;; esac
    case "$(gsettings get org.gnome.desktop.interface gtk-theme 2>/dev/null)" in *-dark*|*-Dark*) return 0 ;; esac
    return 1
}

put() {  # put SRC DST: copy only when different
    cmp -s "$1" "$2" 2>/dev/null && return 0
    mkdir -p "$(dirname "$2")" && cp "$1" "$2.tmp" && mv -f "$2.tmp" "$2"
}

apply() {
    if is_dark; then
        put "$SRC/scalable/apps/$ID-dark.svg" "$BASE/scalable/apps/$ID.svg"
        for s in $SIZES; do
            [ -f "$SRC/${s}x${s}/apps/$ID-dark.png" ] && put "$SRC/${s}x${s}/apps/$ID-dark.png" "$BASE/${s}x${s}/apps/$ID.png"
        done
    else
        rm -f "$BASE/scalable/apps/$ID.svg"
        for s in $SIZES; do rm -f "$BASE/${s}x${s}/apps/$ID.png"; done
    fi
    touch "$BASE" "$BASE/.." 2>/dev/null || true  # make the shell re-read the icon theme
}

apply
gsettings monitor org.gnome.desktop.interface 2>/dev/null | while read -r line; do
    case "$line" in *color-scheme*|*gtk-theme*) apply ;; esac
done
