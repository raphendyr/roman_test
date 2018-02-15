#!/bin/sh -e
set -x

version=${TRAVIS_TAG:-}
pyver=${TRAVIS_PYTHON_VERSION:-${PYENV_VERSION}}

if [ "$BUILD_DIST" = 'true' ]; then
	if [ "$TRAVIS_OS_NAME" = 'osx' ]; then
		# pyenv
		PYENV_ROOT="$HOME/.pyenv-roman"
		PATH="$PYENV_ROOT/bin:$PATH"
		hash -r
		eval "$(pyenv init -)"
		hash -r
		PYENV_VERSION=$(pyenv install --list|tr -d '[ \t]'|grep "^$PYENV_VERSION"|tail -n1)

		pip install . simple_gui/
		pip install -r requirements_build_osx.txt

		# wheel distribution
		python setup.py bdist_wheel

		# pyinstaller app image in dmg and zip
		appid=$(grep __app_id__ apluslms_roman/__init__.py|head -n1|cut -d"'" -f2)
		pyinstaller --noconsole --onefile --name Roman --icon simple_gui/roman.icns --osx-bundle-identifier="$appid" simple_gui/roman_tki.py
		hdiutil create dist/roman-gui-$version-mac.dmg -srcfolder dist/ -ov
		(cd dist && zip -r roman-gui-$version-mac.zip Roman.app)
	else
		pip install . simple_gui/
		pip install -r requirements_build_linux.txt

		# source distribution
		python setup.py sdist

		# pyinstaller binary in zip
		pyinstaller --noconsole --onefile --name roman --add-data simple_gui/roman.png:. simple_gui/roman_tki.py
		(cd dist && zip -r roman-gui-$version-linux.zip roman)

		# pyinstaller dir in appimage
		release="https://github.com/AppImage/AppImageKit/releases/download/10"
		dir=dist/Roman.AppDir
		mkdir -p $dir
		pyinstaller --noconsole --name Roman --add-data simple_gui/roman.png:. simple_gui/roman_tki.py
		mv dist/Roman dist/Roman.AppDir/usr/
		sed 's,^Exec=.*$,Exec=./Roman,' simple_gui/roman.desktop > $dir/roman.desktop
		ln -sT usr/roman.png dist/Roman.AppDir/roman.png
		(cd $dir && wget "$release/AppRun-x86_64" -O AppRun && chmod +x AppRun)
		(cd dist && \
		 wget "$release/appimagetool-x86_64.AppImage" && chmod +x appimagetool-x86_64.AppImage && \
		 ./appimagetool-x86_64.AppImage --appimage-extract && \
		 ./squashfs-root/AppRun --comp xz Roman.AppDir && \
		 mv Roman-x86_64.AppImage Roman-gui-$version-linux.AppImage && \
		 rm -rf appimagetool-x86_64.AppImage squashfs-root Roman.AppDir)
	fi
fi
