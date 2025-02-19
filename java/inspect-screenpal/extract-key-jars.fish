#!/usr/bin/env fish

echo "wipe dir if wanna start from scratch"
echo "    trash ~/repos/scratch/extract-screenpal"

mkdir -p ~/repos/scratch/extract-screenpal/app
mkdir -p ~/repos/scratch/extract-screenpal/Library

cp /Applications/ScreenPal.app/Contents/app/AppMain-3.1.10.jar ~/repos/scratch/extract-screenpal/app
cp ~/Library/ScreenPal-v3/v3.16.0/*.jar ~/repos/scratch/extract-screenpal/Library
