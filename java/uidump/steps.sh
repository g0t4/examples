# 1) Compile
javac UiDumpAgent.java AttachAndLoad.java

# 2) Create agent JAR (manifest with Agent-Class)
echo -e "Manifest-Version: 1.0\nAgent-Class: UiDumpAgent\n" > manifest.mf
jar cfm ui-dump-agent.jar manifest.mf UiDumpAgent.class

# 3) Find target JVM pid
jps -l    # or: ps aux | grep java

# 4) Attach (tools attach needs a JDK; run this with `java` from a JDK)
java --add-modules jdk.attach AttachAndLoad <PID> $(pwd)/ui-dump-agent.jar
# Output goes to: /tmp/ui-dump-<PID>.txt
