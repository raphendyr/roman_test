#!/bin/sh -e

src=$1
dest=${2%.icns}
iconset=$dest.iconset
icns=$dest.icns

[ "$src" -a -e "$src" ] || { echo "Icon source missing, not found '$src'" >&2; exit 1; }

if [ "$icns" -nt "$src" ]; then
    echo "No update needed for $icns"
    exit 0
fi

[ -e "$iconset" ] && rm -rf "$iconset"
mkdir -p "$iconset"
(
 sips -z 16 16   "$src" --out "$iconset/icon_16x16.png"
 sips -z 32 32   "$src" --out "$iconset/icon_16x16@2x.png"
 sips -z 32 32   "$src" --out "$iconset/icon_32x32.png"
 sips -z 64 64   "$src" --out "$iconset/icon_32x32@2x.png"
 sips -z 128 128 "$src" --out "$iconset/icon_128x128.png"
 sips -z 256 256 "$src" --out "$iconset/icon_128x128@2x.png"
 sips -z 256 256 "$src" --out "$iconset/icon_256x256.png"
 sips -z 512 512 "$src" --out "$iconset/icon_256x256@2x.png"
 sips -z 512 512 "$src" --out "$iconset/icon_512x512.png"
 cp              "$src"       "$iconset/icon_512x512@2x.png"
) >/dev/null
iconutil -c icns "$iconset"
rm -r "$iconset"

echo "Created $icns from $src"
