#!/bin/sh -e

scripts=$(dirname "$0")
res=$scripts/res/

apppath=$1
dmgpath=$2
[ "$apppath" -a -e "$apppath" ] || { echo "ERROR: missing .app file '$apppath'"; exit 1; }
[ "$dmgpath" ] || { echo "ERROR: missing .dmg filename"; exit 1; }

name=$(basename "${apppath%.app}")
dist=$(dirname "$dmgpath")

bg1=$res/dmg-background.png
bg2=$res/dmg-background@2x.png
dss=$res/DS_Store

require_dpi() {
  f=$1
  i=$2
  if [ ! -e "$f" ]; then
    echo "ERROR: missing image $f"
    exit 1
  fi
  dpi=$(sips -g dpiHeight "$f" | egrep '^\s*dpiHeight' | awk '{print $2}')
  if [ "$dpi" != "$i" ]; then
    echo "ERROR: wrong dpi $dpi expected $i, file $f"
    exit 1
  fi
}

require_dpi "$bg1" "72.000"
require_dpi "$bg2" "144.000"

tmp="$dist/$name"
[ -e "$tmp" ] && rm -rf "$tmp"
mkdir -p "$tmp/.background/"

cp -r "$apppath" "$tmp/"
cp "$bg1" "$tmp/.background/dmg-background.png"
cp "$bg2" "$tmp/.background/dmg-background@2x.png"
cp "$dss" "$tmp/.DS_Store"

SetFile -a icnv "$tmp/.background" "$tmp/.DS_Store"
ln -s /Applications "$tmp/Applications"

[ -e "$dmgpath" ] && rm -f "$dmgpath"
hdiutil create "$dmgpath" \
  -format UDZO -imagekey zlib-level=9 \
  -volname "$name" -srcfolder "$tmp/" -ov
rm -rf "$tmp"
