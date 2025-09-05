javac UiDumpAgent2.java
echo -e "Manifest-Version: 1.0\nAgent-Class: UiDumpAgent2\n" > mf2.mf
jar cfm ui-dump-agent2.jar mf2.mf UiDumpAgent2.class
java --add-modules jdk.attach AttachAndLoad 18560 $(pwd)/ui-dump-agent2.jar
# Check: /tmp/ui-dump-18560.txt and /tmp/ui-dump-18560.log
