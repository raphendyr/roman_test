#!/bin/sh -e

. .travis/_include.sh
set -x


if [ "${BUILD_SDIST:-}" = 'true' ]; then
	run_for_all setup_dist sdist
fi

if [ "${BUILD_GUI:-}" = 'true' ]; then
	appid=$(grep -E '^__app_id__\s*=' "simple_gui/roman_tki.py"|head -n1|cut -d"'" -f2)
	libver=$(grep '^Version: ' "apluslms_roman.egg-info/PKG-INFO" | head -n1 | cut -d ' ' -f 2)
	guiver=$(grep '^Version: ' "simple_gui/apluslms_roman_tki.egg-info/PKG-INFO" | head -n1 | cut -d ' ' -f 2)
	version="$guiver-$libver"

	for package in $PACKAGES simple_gui; do
		path="$BUILD_PATH/$(run_for "$package" setup_py --name)/lib"
		if [ -e "$path" ]; then
			PYTHONPATH="$PYTHONPATH:$path"
		fi
	done
	export PYTHONPATH

	if [ "$TRAVIS_OS_NAME" = 'osx' ]; then
		# create icns
		./packaging/osx/convert_png_to_icns.sh "simple_gui/roman.png" "$BUILD_PATH/roman.icns"

		# create Roman.app
		pyinst packaging/osx/roman_app.spec

		# create .dmg
		./packaging/osx/create_dmg.sh "$DIST_PATH/Roman.app" "$DIST_PATH/Roman-$version-mac-unsigned.dmg"

		# create .zip
		(cd "$DIST_PATH" && zip -r Roman-$version-mac-unsigned.zip Roman.app)

	elif [ "$TRAVIS_OS_NAME" = 'linux' ]; then
		# pyinstaller binary in zip
		pyinst packaging/linux/roman_exe.spec
		(cd "$DIST_PATH" && zip -r Roman-$version-linux.zip Roman)

		# pyinstaller dir in appimage
		pyinst packaging/linux/roman_appimage.spec
		./packaging/linux/create_appimage.sh -i "$appid" -n Roman -l simple_gui/roman.png -d simple_gui/roman_tki.desktop -a simple_gui/roman_tki.appdata.xml "$DIST_PATH/roman_appdata"
		mv "$DIST_PATH/Roman-x86_64.AppImage" "$DIST_PATH/Roman-$version-linux.AppImage"
	fi
fi
