#!/usr/bin/env fish

#export APPDIR=/Applications/ScreenPal.app/Contents/app
export APPDIR=/Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app


# java \
export JAVA_TOOL_OPTIONS="    -Djpackage.app-version=3 
    -Dapple.awt.enableTemplateImages=true 
    -Djava.system.class.loader=DynamicURLClassLoader 
    -Dsom.exe.path=$APPDIR/XXXNOEXE 
    -Dsom.mac.app=$APPDIR/../.. 
    -Dsom.mac.app.launcher=$APPDIR/ScreenPal.app 
    -Dsom.mac.app.tray=$APPDIR/ScreenPalTray.app 
    -Dsp.installer.version=3.0.2.0 
    -Dsun.java2d.opengl=true 
    -Xmx2G
"


# java \
/Users/wesdemos/repos/github/swingexplorer/swingexplorer/dist/SwingExplorer-1.8.0-SNAPSHOT/bin/swexpl \
    -cp "$APPDIR/AppMain-3.0.2.jar:$APPDIR/proxy-selector.jar:$APPDIR/rhino-1.7.14.jar" \
    ScreenPal \
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
    -Xmx2G
