# goal is to modify properties file in a jar file to disable tray for screenpal if possible

cd /Users/wesdemos/Library/ScreenPal-v3
jar tf v3.16.0/ScreencastOMaticEditor-3.16.0-beta6.jar | grep 

# actually it is in diff file
cd /Applications/ScreenPal.app/Contents/app/AppMain-3.1.10.jar
# *** jar ~= tar (as far as args go) - and bsdtar can work with jar files
# jar uses DEFALTE compression
jar tf AppMain-3.1.10.jar
jar -tf AppMain-3.1.10.jar
# AppMain/app.properties

jar -tf AppMain-3.1.10.jar  # list files in AppMain dir
jar -tvf AppMain-3.1.10.jar # verbose list... like ls -al

# FYI bsdtar works too (macOS)
tar -tf AppMain-3.1.10.jar # list files too
tar -xf AppMain-3.1.10.jar # extract files
# gnu tar (no bueno) - at least not on ubuntu (might be args to pass to compile support for deflate)


# backup original
cp AppMain-3.1.10.jar AppMain-3.1.10.jar.original
# also just wipe and reinstall screenpal is fine too

# * mod ownership
# add group write:
sudo chmod -R g+w /Applications/ScreenPal.app/
# match original owner:
sudo chown -R root:admin /Applications/ScreenPal.app/


# test first:
cp /Applications/ScreenPal.app/Contents/app/AppMain-3.1.10.jar ~/Downloads/tmp/
cd ~/Downloads/tmp/

# read file contents w/o extract
unzip -c AppMain-3.1.10.jar app.properties # useful to validate changes
unzip -c AppMain-3.1.10.jar # entire archive all contents
unzip -c AppMain-3.1.10.jar | grep -i foo # great to find smth


# replace!
jar uf AppMain-3.1.10.jar app.properties # update
jar --update --file AppMain-3.1.10.jar app.properties

# verify
unzip -c AppMain-3.1.10.jar app.properties | grep tray

# OK screenpal fails to start so I put back original AppMain-3.1.10.jar

# went back to that partner file I found
cat /Applications/ScreenPal.app/Contents/app/partner_app.properties
# ok I think I need to update the properties here! not in the jar!!!
cd /Applications/ScreenPal.app/Contents/app/
cp partner_app.properties partner_app.properties.original

nvim /Applications/ScreenPal.app/Contents/app/partner_app.properties

# OH FUCK YES... NO MOTHER FUCKING TRAY APP!!!!!!!!! FINALLY FUCK FUCK FUCKERS... I asked if I could disable it... they never responded!
# ... I can change alot of things it seems.. including classes that are loaded by the app!!
#     can I change out for less gpu intensive graphics elements?
#     seems if I were to whitelabel I could change much of the UI to maybe less GPU/CPU intense interfaces that I don't give a FLYING FUCK ABOUT

# OMG... there is this too in app.properties
#   app.version.check.url=DEFAULTHOST/check_latest_versions?currentVersion=CURRENT_VERSION&osName=OS_NAME&osVersion=OS_VERSION
#   I SMELL A FIX FOR MY swexpl problem! with version 2.9.2 b/c 3.16.0 don't load

