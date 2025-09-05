#!/usr/bin/env fish

javac HelloAgent.java
echo -e "Manifest-Version: 1.0\nAgent-Class: HelloAgent\n" > mf.mf
jar cfm hello-agent.jar mf.mf HelloAgent.class
# java --add-modules jdk.attach AttachAndLoad 18560 $(pwd)/hello-agent.jar
# Expect: /tmp/agent-ok-18560.txt
