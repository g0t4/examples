#!/usr/bin/env fish

export PATH="$(/usr/libexec/java_home -v 19)/bin:$PATH"

make clean

mkdir -p build/reloader
javac -d build/reloader reloader/com/reloader/ReloaderAgent.java

mkdir -p build/agenty
javac -d build/agenty agenty/com/agenty/Agenty.java

mkdir -p build/reloader/META-INF
mkdir -p build/agenty/META-INF

printf 'Manifest-Version: 1.0\nImplementation-Version: %s\n' (git rev-parse --short HEAD) > build/agenty/META-INF/MANIFEST.MF

echo "Manifest-Version: 1.0
Premain-Class: com.reloader.ReloaderAgent
Agent-Class: com.reloader.ReloaderAgent
Can-Redefine-Classes: true
Can-Retransform-Classes: true" >build/reloader/META-INF/MANIFEST.MF

mkdir -p dist
jar cfm dist/reloader.jar build/reloader/META-INF/MANIFEST.MF -C build/reloader .
jar cfm dist/agenty.jar build/agenty/META-INF/MANIFEST.MF -C build/agenty .

