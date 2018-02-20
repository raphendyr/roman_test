#!/bin/sh -e

name=roman

mkdir $name.iconset
(
 sips -z 16 16   $name.png --out $name.iconset/icon_16x16.png
 sips -z 32 32   $name.png --out $name.iconset/icon_16x16@2x.png
 sips -z 32 32   $name.png --out $name.iconset/icon_32x32.png
 sips -z 64 64   $name.png --out $name.iconset/icon_32x32@2x.png
 sips -z 128 128 $name.png --out $name.iconset/icon_128x128.png
 sips -z 256 256 $name.png --out $name.iconset/icon_128x128@2x.png
 sips -z 256 256 $name.png --out $name.iconset/icon_256x256.png
 sips -z 512 512 $name.png --out $name.iconset/icon_256x256@2x.png
 sips -z 512 512 $name.png --out $name.iconset/icon_512x512.png
 cp              $name.png       $name.iconset/icon_512x512@2x.png
) >/dev/null
iconutil -c icns $name.iconset
rm -R $name.iconset

echo "created $name.icns"
