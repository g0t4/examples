#!/usr/bin/env fish

export APPDIR=/Applications/ScreenPal.app/Contents/app


# *** OK SO -D et al CANNOT COME AFTER ScrenPal (class name)... 
# **** OK LAST THING TO SOLVE (see app-0.log in ~/Library/ScreenPal-v3/app-0.log) ... why it doesn't try v3.16.0.. it keeps trying 2.9.2 and that fails cuz its not downloaded... this is last issue, why is it trying 2.9.2!!!!!
#   even solve this with test.fish and why it suggests to download 2.9.2 as newer vesrion... vs standalone which doesn't do this... hrm
#  CAN I FIND AN ENV VAR MAYBE OR WHAT... smth in Info.plist for .app that controls this?!
#   OK WEIRD... this tries to load 3.16.0 and fails so it deletes it!
#     02/19/25 02:28:29 WARN T0001: Failed to use current version folder so trying to delete: /Users/wesdemos/Library/ScreenPal-v3/v3.16.0
#        have to load .app again to get it to bring back 3.16.0
# *** BTW ... IIRC version.txt dictates what one is used... I just added that and maybe that is why it is now deleting 3.16.0 when it "doesn't work"


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
    -Djpackage.app-version=3 \
    --add-opens java.desktop/java.awt=ALL-UNNAMED \
    --add-opens java.desktop/java.awt.event=ALL-UNNAMED --add-opens java.desktop/java.awt.peer=ALL-UNNAMED \
    --add-opens java.desktop/javax.swing=ALL-UNNAMED --add-opens java.desktop/javax.swing.plaf.basic=ALL-UNNAMED \
    --add-opens java.desktop/javax.swing.text=ALL-UNNAMED --add-opens java.desktop/sun.awt=ALL-UNNAMED \
    --add-opens java.desktop/sun.lwawt=ALL-UNNAMED --add-opens java.desktop/sun.lwawt.macosx=ALL-UNNAMED \
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
    -cp /Users/wesdemos/repos/github/swingexplorer/swingexplorer/dist/SwingExplorer-1.8.0-SNAPSHOT/swingexplorer-core-1.8.0-SNAPSHOT.jar:/Users/wesdemos/repos/github/swingexplorer/swingexplorer/dist/SwingExplorer-1.8.0-SNAPSHOT/lib/swing-layout-1.0.3.jar:$APPDIR/AppMain-3.0.2.jar:$APPDIR/proxy-selector.jar:$APPDIR/rhino-1.7.14.jar \
    org.swingexplorer.Launcher \
    ScreenPal


# OK ISSUE IS ALSO ORDER OF PARAMS!!!!!! do not put -D after!
#   and then it starts almost all the way up with swexpl... just tries to load 2.9.2 and fails
# !!! now last issue is that

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
