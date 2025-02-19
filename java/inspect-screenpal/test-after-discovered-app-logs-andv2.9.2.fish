#!/usr/bin/env fish

# ***! MUST SET APPDIR else fails on splash screen exception
export APPDIR=/Applications/ScreenPal.app/Contents/app
#export APPDIR=/Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app
# both dirs work btw
#  TODO!! some how there is a notice to download an older version of SPAL! TODO FIND OUT WHAT IS WRONG
#    FOR NOW ONLY UPDATE AFTER LAUNCHING with the actual app and not this script...then it doesn't show the old version as an update
# 

# FYI! THIS IS BASED on jpackage config file for ScreenPal
# see this: /Applications/ScreenPal.app/Contents/app/ScreenPal.cfg


# FYI THIS WAS WORKING and I DID NOT CHANGE IT and IT NOW FAILS
# FUU this isn't working now... smth smells off.. is it possible I am detectin different downloads of SOM/SPAL... and starting diff ones...
# *** app log has more!
# cat /Users/wesdemos/Library/ScreenPal-v3/app-0.log
# !!! SHIT ITS LOADING v 2.9.2!!! WTF
#      App Tmp Dir Set: /Users/wesdemos/Library/ScreenPal-v2/
#    issue?   this log has     som.appdata.path="null"
#   FYI start it regularly and review app log for differences
#      regular was failing wiht 2.9.2 present!!!!!
#        ok 2.9.2. is what is suggested for download by this script (when this works, after remove 2.9.2 this then works again)
# ***! TRYING TO USE swexpl TRIGGERED THE DOWNLOAD of 2.9.2
#     still feels like some args aren't getting passed... TBD see if can fix later
# !! DIFF LOGS to find diff in app-0.log between run .app vs this test.fish... what is causing 2.9.2 to be downloaded or suggestedo??
#   

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
    -Djava.system.class.loader=DynamicURLClassLoader \
    -Dapple.awt.enableTemplateImages=true \
    -Dsom.exe.path=$APPDIR/XXXNOEXE \
    -Dsom.mac.app=$APPDIR/../.. \
    -Dsom.mac.app.launcher=$APPDIR/ScreenPal.app \
    -Dsom.mac.app.tray=$APPDIR/ScreenPalTray.app \
    -Dsp.installer.version=3.0.2.0 \
    -Dsun.java2d.opengl=true \
    -Xmx2G \
    -cp "$APPDIR/AppMain-3.0.2.jar:$APPDIR/proxy-selector.jar:$APPDIR/rhino-1.7.14.jar" \
    ScreenPal
