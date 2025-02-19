#!/usr/bin/env fish

# TODO UPDATE VERSION as needed
set screenpal_version "v3.16.0"
echo "extracting version: $screenpal_version"

# echo "wipe dir if wanna start from scratch"
# echo "    trash ~/repos/scratch/extract-screenpal"

mkdir -p ~/repos/scratch/extract-screenpal/app
mkdir -p ~/repos/scratch/extract-screenpal/$screenpal_version

cp /Applications/ScreenPal.app/Contents/app/AppMain-3.1.10.jar ~/repos/scratch/extract-screenpal/app
cp ~/Library/ScreenPal-v3/$screenpal_version/*.jar ~/repos/scratch/extract-screenpal/$screenpal_version

# app
# -o = overwrite existing files (otherwise it prompts)
for jar in ~/repos/scratch/extract-screenpal/app/*.jar
    unzip -o -d $jar-expand $jar
end

# lib
for jar in ~/repos/scratch/extract-screenpal/$screenpal_version/*.jar
    unzip -o -d $jar-expand $jar
end

echo "DONE => cd ~/repos/scratch/extract-screenpal/"
echo "     ag -G properties tray" 

# nuke other languages to cleanup search for properties
# ag -ig "_pt_br"
# ls **/*_*.properties
# trash **/*_pt_br.properties
# trash **/*_de.properties
# trash **/*_es.properties
# trash **/*_fr.properties
# trash **/*_it.properties
# trash **/*_ja.properties
# trash **/*_zh.properties
# 
# # now this works beter
# ag  -G properties tray
