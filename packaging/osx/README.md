OS X Packaging
==============

Packing for OS X is bit interesting.
Here are utilities to manage packaging configuration and to create final disk image.

Finder background
-----------------

Disk image is oppened with a Finder window and we use background image to render information texts.
Source file is in `res/dmg-background.svg` and 72DPI and 144DPI renders in `res/dmg-background.png` and `res/dmg-background@2x.png` respectively.

.DS_Store
---------

DMG installer contains Finder window layout and background in a binary file `.DS_Store`.
Apple has not documented this format.

Tool `setup_volume.sh` is used to create test volume for modifying DS_Store file.
It uses an applescript to create layout.
You can edit the script to test new layout parameters.
Though, resulting DS_Store contains volume mounts and other irrelevant information and thus can not be used for distributing.
For distributable version, there is node script in `createdbstore` directory.

So, first play with the `setup_volume.sh` and applescript to get window that looks correct and then recreate the configuration with `createdbstore`.
Finally, copy `.DS_Store` to `res/DS_store`.

Creating final image
--------------------

Script `create_dmg.sh` creates compressed read-only disk image.
It uses resources from `res` directory.
It requires the destination as parameter.

For example `./packaging/osx/create_dmg.sh dist/roman.dmg`.
