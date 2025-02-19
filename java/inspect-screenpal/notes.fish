# find java processes
jps -lvm 
# 30261 ScreenPal tray -Djpackage.app-version=3 --add-opens=java.desktop/java.awt=ALL-UNNAMED --add-opens=java.desktop/java.awt.event=ALL-UNNAMED --add-opens=java.desktop/java.awt.peer=ALL-UNNAMED --add-opens=java.desktop/javax.swing=ALL-UNNAMED --add-opens=java.desktop/javax.swing.plaf.basic=ALL-UNNAMED --add-opens=java.desktop/javax.swing.text=ALL-UNNAMED --add-opens=java.desktop/sun.awt=ALL-UNNAMED --add-opens=java.desktop/sun.lwawt=ALL-UNNAMED --add-opens=java.desktop/sun.lwawt.macosx=ALL-UNNAMED -Dapple.awt.enableTemplateImages=true -Djava.system.class.loader=DynamicURLClassLoader -Dsom.exe.path=/Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app/XXXNOEXE -Dsom.mac.app=/Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app/../.. -Dsom.mac.app.launcher=/Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app/ScreenPal.app -Dsom.mac.app.tray=/Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app/ScreenPalTray.app -Dsp
# 30182 ScreenPal -Djpackage.app-version=3 --add-opens=java.desktop/java.awt=ALL-UNNAMED --add-opens=java.desktop/java.awt.event=ALL-UNNAMED --add-opens=java.desktop/java.awt.peer=ALL-UNNAMED --add-opens=java.desktop/javax.swing=ALL-UNNAMED --add-opens=java.desktop/javax.swing.plaf.basic=ALL-UNNAMED --add-opens=java.desktop/javax.swing.text=ALL-UNNAMED --add-opens=java.desktop/sun.awt=ALL-UNNAMED --add-opens=java.desktop/sun.lwawt=ALL-UNNAMED --add-opens=java.desktop/sun.lwawt.macosx=ALL-UNNAMED -Dapple.awt.enableTemplateImages=true -Djava.system.class.loader=DynamicURLClassLoader -Dsom.exe.path=/Applications/ScreenPal.app/Contents/app/XXXNOEXE -Dsom.mac.app=/Applications/ScreenPal.app/Contents/app/../.. -Dsom.mac.app.launcher=/Applications/ScreenPal.app/Contents/app/ScreenPal.app -Dsom.mac.app.tray=/Applications/ScreenPal.app/Contents/app/ScreenPalTray.app -Dsp.installer.version=3.0.2.0 -Dsun.java2d.opengl=true -Xmx2G -Djpackage.app-path=/Applications/ScreenPal.app/Contents/MacOS/ScreenPal
# NOTE ignore the jps matched process (itself)

pstree -p 30261
#─┬◆ 00001 root /sbin/launchd
# └──◆ 30261 wesdemos /Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/MacOS/ScreenPal tray
#
pstree -p 30182
#─┬◆ 00001 root /sbin/launchd
# └─┬◆ 30182 wesdemos /Applications/ScreenPal.app/Contents/MacOS/ScreenPal
#   ├─── 30231 wesdemos <defunct>
#   └─── 30257 wesdemos /Users/wesdemos/Library/ScreenPal-v3/som_nl 149

# *** ScreenPal seems to be the one I am after (the editor)...
# kill tray:
pkill -ilf -ilf "ScreenPal tray"
# kill -15 30261

jps -lvm
# 30182 ScreenPal ... <SAME AS ABOVE>

# FYI this works on my own, obviously:
 ./ScreenPal   -Djpackage.app-version=3 --add-opens=java.desktop/java.awt=ALL-UNNAMED --add-opens=java.desktop/java.awt.event=ALL-UNNAMED --add-opens=java.desktop/java.awt.peer=ALL-UNNAMED --add-opens=java.desktop/javax.swing=ALL-UNNAMED --add-opens=java.desktop/javax.swing.plaf.basic=ALL-UNNAMED --add-opens=java.desktop/javax.swing.text=ALL-UNNAMED --add-opens=java.desktop/sun.awt=ALL-UNNAMED --add-opens=java.desktop/sun.lwawt=ALL-UNNAMED --add-opens=java.desktop/sun.lwawt.macosx=ALL-UNNAMED -Dapple.awt.enableTemplateImages=true -Djava.system.class.loader=DynamicURLClassLoader -Dsom.exe.path=/Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app/XXXNOEXE -Dsom.mac.app=/Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app/../.. -Dsom.mac.app.launcher=/Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app/ScreenPal.app -Dsom.mac.app.tray=/Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app/ScreenPalTray.app -Dsp

# so, som_nl is a child process, not sure what for?

# now go unzip AppMain
mkdir tmp
# copy AppMain.jar
#   why does this nested dir exist too? => it all seems to point here /Applications/ScreenPal.app/Contents/app... oh well use the values from what is running
cp -r /Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app/*.jar .
for i in *.jar; unzip -d $i-expand $i; end

# cd into AppMain-3.0.2.jar-expand/
javap -c -p AppMain.class
#     public static void main(java.lang.String[]);
procyon # linq inspired reflection, decopmiler, etc 
#https://github.com/mstrobel/procyon
procyon-decompiler  AppMain.class  # MUCH NICER!

# ScreenPal exe... btw
/Applications/ScreenPal.app/Contents/MacOS/ScreenPal
strings /Applications/ScreenPal.app/Contents/MacOS/ScreenPal
# appears to use jpackage... lookk at cfg:
cat /Applications/ScreenPal.app/Contents/app/NoSplashScreen/ScreenPal.app/Contents/app/ScreenPal.cfg 
# DO A LITTLE DANCE! CHA CHING
# !!! GOT IT WORKING with test.fish (all params and what not figured out)
#   *** do not forget to set APPDIR!
#   TODO IF ANY ISSUES,  see if I am missing any other env vars (w/o APPDIR it crashes on splash screen failure)


# interesting... there is a partner build thingy in the app
cat /Applications/ScreenPal.app/Contents/app/partner_app.properties
# This file is read after AppMainXxx.jar's app.properties, app_default.properties, and locale (like app_es.properties)
# to let a custom Partner build override any of those app properties, like "app.updateonstart.title=ScreenPal" could
# be replaced with a Partner's brand.
# ! THEY HAVE whitelabeling for the app, I forgot about that... also has package key if I need to re-sign?


