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
#   WOA was LOADING v 2.9.2
#      App Tmp Dir Set: /Users/wesdemos/Library/ScreenPal-v2/
#    issue?   this log has     som.appdata.path="null"
#   FYI start it regularly and review app log for differences
#      regular was failing wiht 2.9.2 present!!!!!
#        ok 2.9.2. is what is suggested for download by this script (when this works, after remove 2.9.2 this then works again)
# ***! TRYING TO USE swexpl TRIGGERED THE DOWNLOAD of 2.9.2
#        FYI app-0.log => you can see args aren't passed correctly... one has URL w/ comman delimited args in URL?!
#           major diff (run .app vs swexpl => INFO T0001: Running with args: [] ...
#              when i run with test.fish & with app regular luanch ... nothing in args list
#              when I try to use via swexpl... then args show in that list... ... fix this and it wil likely start from swexpl... 
#                  smth with how agent launches the app vs w/o agent (IIUC same issue with intellij to launch it run config)

#           args seem ok actually in log
#              url is messed up but ...
#              this is error:
#                 02/19/25 01:48:46 INFO T0022: UPDATING-STARTING-UP-FRAME: The Splash Screen was not showing.  (The user has not run the newer ScreenPal Installer.)  Opening the Updating/Starting-Up identical looking image of (656, 354, 608, 373).
# ***             No current version found. => hence download 2.9.2
#           Checking previous app port: http://127.0.0.1:56480/-Djpackage.app-version%3D3,--add-opens,java.desktop%2Fjava.awt%3DALL-UNNAMED,--add-opens,java.desktop%2Fjava.awt.event%3DALL-UNNAMED,--add-opens,java.desktop%2Fjava.awt.peer%3DALL-UNNAMED,--add-opens,java.desktop%2Fjavax.swing%3DALL-UNNAMED,--add-opens,java.desktop%2Fjavax.swing.plaf.basic%3DALL-UNNAMED,--add-opens,java.desktop%2Fjavax.swing.text%3DALL-UNNAMED,--add-opens,java.desktop%2Fsun.awt%3DALL-UNNAMED,--add-opens,java.desktop%2Fsun.lwawt%3DALL-UNNAMED,--add-opens,java.desktop%2Fsun.lwawt.macosx%3DALL-UNNAMED,-splash%3A%2FApplications%2FScreenPal.app%2FContents%2Fapp%2FScreenPalSplashScreen.png,-Dapple.awt.enableTemplateImages%3Dtrue,-Djava.system.class.loader%3DDynamicURLClassLoader,-Dsom.exe.path%3D%2FApplications%2FScreenPal.app%2FContents%2Fapp%2FXXXNOEXE,-Dsom.mac.app%3D%2FApplications%2FScreenPal.app%2FContents%2Fapp%2F..%2F..,-Dsom.mac.app.launcher%3D%2FApplications%2FScreenPal.app%2FContents%2Fapp%2FScreenPal.app,-Dsom.mac.app.tray%3D%2FApplications%2FScreenPal.app%2FContents%2Fapp%2FScreenPalTray.app,-Dsp.installer.version%3D3.0.2.0,-Dsun.java2d.opengl%3Dtrue,-Xmx2G
#           as if it is checking for a new version from this location... what are the args to pass? in what order or?
# !!! ARGS are likely messed up still in swexpl case
#     still feels like some args aren't getting passed... TBD see if can fix later
# !! DIFF LOGS to find diff in app-0.log between run .app vs this test.fish... what is causing 2.9.2 to be downloaded or suggestedo??
#   
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
