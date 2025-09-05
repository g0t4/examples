#!/usr/bin/env fish

export PATH="$("/usr/libexec/java_home" -v 19)/bin:$PATH"

# * cleanup
trash *.class *.jar

# * build
javac SleepMain.java HelloAgent.java AttachAndLoad.java
printf "Manifest-Version: 1.0\nAgent-Class: HelloAgent\nCan-Retransform-Classes: true\nCan-Redefine-Classes: true\n\n" >MANIFEST.MF
jar cfm hello-agent.jar MANIFEST.MF HelloAgent.class
