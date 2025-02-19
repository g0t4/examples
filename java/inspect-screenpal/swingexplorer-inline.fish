#!/usr/bin/env fish

export APPDIR=/Applications/ScreenPal.app/Contents/app

#export APPDIR=/Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app # doesn't have splash screen png here too.. hrm

# FYI MAKE SURE APPDIR is working below

# TODO export SWEXPLDIR=/Users/wesdemos/repos/github/swingexplorer/swingexplorer/dist/SwingExplorer-1.8.0-SNAPSHOT

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
    -Xshare:off
"
# !!!! this issue appears to be that the args really are not getting passed still to the app... if I comment out JAVA_TOOL_OPTIONS above then it fails earlier (in launch of spal... as if swingexplorer is not passing the args below still

# This comes from inlining what swexpl (bash script) does... easier to tinker with this
java -javaagent:/Users/wesdemos/repos/github/swingexplorer/swingexplorer/dist/SwingExplorer-1.8.0-SNAPSHOT/swingexplorer-agent-1.8.0-SNAPSHOT.jar \
    -Xbootclasspath/a:/Users/wesdemos/repos/github/swingexplorer/swingexplorer/dist/SwingExplorer-1.8.0-SNAPSHOT/swingexplorer-agent-1.8.0-SNAPSHOT.jar:/Users/wesdemos/repos/github/swingexplorer/swingexplorer/dist/SwingExplorer-1.8.0-SNAPSHOT/lib/javassist-3.12.1.GA.jar \
    -cp /Users/wesdemos/repos/github/swingexplorer/swingexplorer/dist/SwingExplorer-1.8.0-SNAPSHOT/swingexplorer-core-1.8.0-SNAPSHOT.jar:/Users/wesdemos/repos/github/swingexplorer/swingexplorer/dist/SwingExplorer-1.8.0-SNAPSHOT/lib/swing-layout-1.0.3.jar:$APPDIR/AppMain-3.0.2.jar:$APPDIR/proxy-selector.jar:$APPDIR/rhino-1.7.14.jar \
    org.swingexplorer.Launcher ScreenPal \
    " -Djpackage.app-version=3 
    --add-opens java.desktop/java.awt=ALL-UNNAMED 
    --add-opens java.desktop/java.awt.event=ALL-UNNAMED --add-opens java.desktop/java.awt.peer=ALL-UNNAMED 
    --add-opens java.desktop/javax.swing=ALL-UNNAMED --add-opens java.desktop/javax.swing.plaf.basic=ALL-UNNAMED
    --add-opens java.desktop/javax.swing.text=ALL-UNNAMED --add-opens java.desktop/sun.awt=ALL-UNNAMED 
    --add-opens java.desktop/sun.lwawt=ALL-UNNAMED --add-opens java.desktop/sun.lwawt.macosx=ALL-UNNAMED
    -splash:$APPDIR/ScreenPalSplashScreen.png 
    -Dapple.awt.enableTemplateImages=true 
    -Djava.system.class.loader=DynamicURLClassLoader 
    -Dsom.exe.path=$APPDIR/XXXNOEXE 
    -Dsom.mac.app=$APPDIR/../.. 
    -Dsom.mac.app.launcher=$APPDIR/ScreenPal.app 
    -Dsom.mac.app.tray=$APPDIR/ScreenPalTray.app 
    -Dsp.installer.version=3.0.2.0 
    -Dsun.java2d.opengl=true 
    -Xmx2G "

# FYI swexpl is just a bash script around java cmd... so if I cannot get it to pass my args then just call it myself
#
## THERE IS STILL SOME ISSUE PASSING ARGS to ScreenPal app ... I modified swexpl to change how args are passed to try to fix it and no joe... 
## java \
#/Users/wesdemos/repos/github/swingexplorer/swingexplorer/dist/SwingExplorer-1.8.0-SNAPSHOT/bin/swexpl \
#    -cp "$APPDIR/AppMain-3.0.2.jar:$APPDIR/proxy-selector.jar:$APPDIR/rhino-1.7.14.jar" \
#    ScreenPal \
#    -Djpackage.app-version=3 \
#    --add-opens java.desktop/java.awt=ALL-UNNAMED \
#    --add-opens java.desktop/java.awt.event=ALL-UNNAMED \
#    --add-opens java.desktop/java.awt.peer=ALL-UNNAMED \
#    --add-opens java.desktop/javax.swing=ALL-UNNAMED \
#    --add-opens java.desktop/javax.swing.plaf.basic=ALL-UNNAMED \
#    --add-opens java.desktop/javax.swing.text=ALL-UNNAMED \
#    --add-opens java.desktop/sun.awt=ALL-UNNAMED \
#    --add-opens java.desktop/sun.lwawt=ALL-UNNAMED \
#    --add-opens java.desktop/sun.lwawt.macosx=ALL-UNNAMED \
#    -splash:$APPDIR/ScreenPalSplashScreen.png \
#    -Dapple.awt.enableTemplateImages=true \
#    -Djava.system.class.loader=DynamicURLClassLoader \
#    -Dsom.exe.path=$APPDIR/XXXNOEXE \
#    -Dsom.mac.app=$APPDIR/../.. \
#    -Dsom.mac.app.launcher=$APPDIR/ScreenPal.app \
#    -Dsom.mac.app.tray=$APPDIR/ScreenPalTray.app \
#    -Dsp.installer.version=3.0.2.0 \
#    -Dsun.java2d.opengl=true \
#    -Xmx2G
