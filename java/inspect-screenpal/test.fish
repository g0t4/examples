#!/usr/bin/env fish

# ***! MUST SET APPDIR else fails on splash screen exception
# export APPDIR=/Applications/ScreenPal.app/Contents/app
export APPDIR=/Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app
# both dirs work btw
#  TODO!! some how there is a notice to download an older version of SPAL! TODO FIND OUT WHAT IS WRONG
#    FOR NOW ONLY UPDATE AFTER LAUNCHING with the actual app and not this script...then it doesn't show the old version as an update
# 

# FYI! THIS IS BASED on jpackage config file for ScreenPal
# see this: /Applications/ScreenPal.app/Contents/app/ScreenPal.cfg

java \
  -Djpackage.app-version=3 \
  --add-opens java.desktop/java.awt=ALL-UNNAMED \
  --add-opens java.desktop/java.awt.event=ALL-UNNAMED \
  --add-opens java.desktop/java.awt.peer=ALL-UNNAMED \
  --add-opens java.desktop/javax.swing=ALL-UNNAMED \
  --add-opens java.desktop/javax.swing.plaf.basic=ALL-UNNAMED \
  --add-opens java.desktop/javax.swing.text=ALL-UNNAMED \
  --add-opens java.desktop/sun.awt=ALL-UNNAMED \
  --add-opens java.desktop/sun.lwawt=ALL-UNNAMED \
  --add-opens java.desktop/sun.lwawt.macosx=ALL-UNNAMED \
  -splash:$APPDIR/ScreenPalSplashScreen.png \
  -Dapple.awt.enableTemplateImages=true \
  -Djava.system.class.loader=DynamicURLClassLoader \
  -Dsom.exe.path=$APPDIR/XXXNOEXE \
  -Dsom.mac.app=$APPDIR/../.. \
  -Dsom.mac.app.launcher=$APPDIR/ScreenPal.app \
  -Dsom.mac.app.tray=$APPDIR/ScreenPalTray.app \
  -Dsp.installer.version=3.0.2.0 \
  -Dsun.java2d.opengl=true \
  -Xmx2G \
  -cp "$APPDIR/AppMain-3.0.2.jar:$APPDIR/proxy-selector.jar:$APPDIR/rhino-1.7.14.jar" \
  ScreenPal

