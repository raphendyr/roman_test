#!/bin/sh -e

scripts=$(dirname "$0")
res=$scripts/res/

name=Roman
vol=$name
dmg=roman-setup.dmg

if [ ! -e "$dmg" ]; then
  if [ ! -d "$name" ]; then
    echo "There is no directory $name/"
    echo "Create template of dmg content in that before running this (create_dms.sh)."
    exit 1
  fi
  size=$(du -sm "$name" | awk '{print $1}')
  size=$(echo "$size + 5" | bc)
  rm -f $name/.DS_Store
  hdiutil create -srcfolder "$name" -volname "$name" -fs HFS+ -fsargs "-c c=64,a=16,e=16" -format UDRW -size ${size}M "$dmg"
  echo "Created: $dmg"
fi

# Detach existing mounts
if [ -d "/Volumes/$vol" ]; then
  dev=$(hdiutil info | egrep '^/dev/' | egrep "/Volumes/$vol" | sed 1q | awk '{print $1}' | cut -ds -f1-2)
  hdiutil --force detach $dev
fi

# Mount, run applescript, wait for enter (manual edit)
dev=$(hdiutil attach -readwrite -noverify "$dmg" | egrep '^/dev/' | sed 1q | awk '{print $1}')
echo "Editing data in /Volumes/$vol, press ENTER when manual edit is done"
osascript $res/finder_layout.scpt
read
hdiutil detach "$dev" >/dev/null

# Remount, read .DS_Store
dev=$(hdiutil attach -readwrite -noverify -noautoopen "$dmg" | egrep '^/dev/' | sed 1q | awk '{print $1}')
cp -v /Volumes/$vol/.DS_store $res/DS_Store
hdiutil detach "$dev" >/dev/null
