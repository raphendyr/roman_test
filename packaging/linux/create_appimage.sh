#!/bin/sh -eu

# pyinstaller dir in appimage
version=11
release="https://github.com/AppImage/AppImageKit/releases/download/$version"
appid=
name=
logo=
desktop=
appdata=
dist=dist
cache=


while [ $# -gt 0 ]; do
    case "$1" in
		-i) appid=$2 ; shift 2 ;;
		-n) name=$2 ; shift 2 ;;
		-l) logo=$2 ; shift 2 ;;
		-d) desktop=$2 ; shift 2 ;;
		-a) appdata=$2 ; shift 2 ;;
        -D) dist=$2 ; shift 2 ;;
		-C) cache=$2 ; shift 2 ;;
        --) shift ; break ;;
        -*) echo "ERROR: Invalid option '$1' for $0" >&2 ; exit 64 ;;
        *) break ;;
    esac
done

app="${1:-$dist/$name}"

if [ -z "$app" -o ! -e "$app" ]; then
	echo "ERROR: app source missing or invalid: app '$app'" >&2
	exit 1
fi

appid=${appid:-$name}
namel=$(echo "$name" | tr '[A-Z]' '[a-z]')
appdir="$app.AppDir"
cache=${cache:-${APPIMAGHE_CACHE:-$PWD/build/appimage_cache}}


copy_apprun() {
	mkdir -p "$cache"
	app_run="$cache/AppRun-$version"
	if ! [ -e "$app_run" ]; then
		wget "$release/AppRun-x86_64" -O "$app_run"
	fi
	cp -v "$app_run" "$1/AppRun"
	chmod a+x "$1/AppRun"
}

appimage() {
	mkdir -p "$cache"
	app_image_dir="$cache/appimagetool-$version"
	if ! [ -e "$app_image_dir" ]; then
		(
			cd "$(dirname "$app_image_dir")"
			wget "$release/appimagetool-x86_64.AppImage"
			chmod +x appimagetool-x86_64.AppImage
			./appimagetool-x86_64.AppImage --appimage-extract
			mv squashfs-root "$(basename "$app_image_dir")"
			rm appimagetool-x86_64.AppImage
		)
	fi
	"$app_image_dir/AppRun" "$@"
}

# create .AppDir
mkdir -p "$appdir"
mv -v "$app" "$appdir/usr"

if [ "$logo" -a -e "$logo" ]; then
	mkdir -p "$appdir/usr/share/$appid/"
	cp -v "$logo" "$appdir/usr/share/$appid/"
	ln -sT "usr/share/$appid/$(basename "$logo")" "$appdir/$(basename "$logo")"
fi

if [ "$desktop" -a -e "$desktop" ]; then
	mkdir -p "$appdir/usr/share/applications"
	sed "s,^Exec=.*\$,Exec=./$name," "$desktop" > "$appdir/usr/share/applications/$appid.desktop"
	echo "created $appdir/usr/share/applications/$appid.desktop"
	ln -sT "usr/share/applications/$appid.desktop" "$appdir/$namel.desktop"
fi

if [ "$appdata" -a -e "$appdata" ]; then
	mkdir -p "$appdir/usr/share/metainfo"
	# FIXME: following should be in path $appdir/usr/share/metainfo/$appid.appdata.xml, but that is not recognized by appimagetool
	sed -e "s,__app_id__,$appid,g" "$appdata" > "$appdir/usr/share/metainfo/$namel.appdata.xml"
	echo "created $appdir/usr/share/metainfo/$namel.appdata.xml"
fi

# copy AppRun
copy_apprun "$appdir"

# build AppImage
(
	cd "$dist"
	appimage --comp xz "${appdir##*/}"
)

# clean
rm -rf "$appdir"
