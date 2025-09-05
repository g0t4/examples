#!/usr/bin/env fish

# ENSURE RIGHT JAVA VERSION
export PATH="$(/usr/libexec/java_home -v 19)/bin:$PATH"
# OR get version spal ships with? 19.0.1, my 19 SDK above is 19.0.2 so it s/b fine

# * cleanup
trash *.class *.jar

# * agent1
javac UiDumpAgent.java AttachAndLoad.java
echo -e "Manifest-Version: 1.0\nAgent-Class: UiDumpAgent\n" >manifest.mf
jar cfm ui-dump-agent.jar manifest.mf UiDumpAgent.class

# java --add-modules jdk.attach AttachAndLoad <PID> $(pwd)/ui-dump-agent.jar
#!/usr/bin/env fish

javac UiDumpAgent2.java
echo -e "Manifest-Version: 1.0\nAgent-Class: UiDumpAgent2\n" >mf2.mf
jar cfm ui-dump-agent2.jar mf2.mf UiDumpAgent2.class
# java --add-modules jdk.attach AttachAndLoad <PID> $(pwd)/ui-dump-agent2.jar
#!/usr/bin/env fish

javac HelloAgent.java
echo -e "Manifest-Version: 1.0\nAgent-Class: HelloAgent\n" >mf.mf
jar cfm hello-agent.jar mf.mf HelloAgent.class
# java --add-modules jdk.attach AttachAndLoad <PID> $(pwd)/hello-agent.jar

# * list JVMs
jps -l
# or: ps aux | grep java
