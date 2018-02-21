tell application "Finder"
  tell disk "Roman"
    open

    set theX to 300
    set theY to 200
    set theW to 760
    set theH to 480
    set theX2 to (theX + theW)
    set theY2 to (theY + theH)
    set theI1X to 200
    set theI2X to (theW - theI1X)
    set theIY to 200

    tell container window
      set current view to icon view
      set toolbar visible to false
      set statusbar visible to false
      set the bounds to {theX, theY, theX2, theY2}
    end tell

    set viewOptions to the icon view options of container window
    tell viewOptions
      set arrangement to not arranged
      set icon size to 128
      set text size to 14
    end tell

    set background picture of viewOptions to file ".background:dmg-background.png"
    set position of item "Roman.app" of container window to {theI1X, theIY}
    set position of item "Applications" of container window to {theI2X, theIY}

    close
    open
    update without registering applications
    delay 2
  end tell
end tell
