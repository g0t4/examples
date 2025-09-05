#!/usr/bin/env fish

export PATH="$(/usr/libexec/java_home -v 19)/bin:$PATH"

make clean

javac -d out src/main/java/your/pkg/DemoAgent.java
jar cfm demo-agent.jar META-INF/MANIFEST.MF -C out .
