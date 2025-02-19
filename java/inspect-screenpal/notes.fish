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

# so, som_nl is a child process, not sure what for?


