#!/bin/sh -e

scripts=$(dirname "$0")
res=$scripts/res/

out=$1
[ "$out" ] || { echo "ERROR: missing output file"; exit 1; }
dist=$(dirname "$out")

name=Roman
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

d=$dist/$name

rm -rf $d
mkdir -p $d/.background/

cp -r $dist/$name.app $d/
cp "$bg1" $d/.background/dmg-background.png
cp "$bg2" $d/.background/dmg-background@2x.png
cp "$dss" $d/.DS_Store

SetFile -a icnv $d/.background $d/.DS_Store
ln -s /Applications $d/Applications

hdiutil create $out \
  -format UDZO -imagekey zlib-level=9 \
  -volname $name -srcfolder $d/ -ov
