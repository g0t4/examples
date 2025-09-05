

working:
```sh
java SleepMain # run separate tab
jps -l # get PID
./jattach 82088 load instrument false hello-agent.jar
# works!


# list cmds
./jattach 18560 jcmd help -all


# useful to see what this app uses (instead of just digging on disk in files)
./jattach 18560 jcmd VM.classes




```

## VisualVM - heapdump has stuff I want!!!
- found controls already! windows by names!
- AND I AM FINDING WHAT I WANT! 
- HeapDump literally has most of what I wanted to read
- so I could  use this myself to get access to internal state
  - i.e. hopefully to read the edit points
  - or to see the silence periods recisely!
  - maybe even get access to the audio/video data w/o needing to export separtely and manage all that.. and instead read and propose edits off of that and then if I edit in reverse I can use that as an edit list for typical edits that don't need my involvement!

## ALSO jcmd is giving me some of what I want too!

```fish


set PID 18560

# list classes and find classes for controls!
./jattach $PID jcmd VM.classes | grep -i window

# floating windows!
./jattach $PID jcmd VM.classes | grep -i FloatingWindow

# primary window (editor)
./jattach $PID jcmd VM.classes | grep -i editorframe

```

## 100/102 attach errors

```fish
z github/openjdk/jdk/src/jdk.attach
# *** source code for attach functionality is right here! BUST IT OUT!
rg "attach.*10"
# share/classes/sun/tools/attach/HotSpotVirtualMachine.java:199:30:    private static final int ATTACH_ERROR_BADJAR        = 100;
# share/classes/sun/tools/attach/HotSpotVirtualMachine.java:200:30:    private static final int ATTACH_ERROR_NOTONCP       = 101;
# share/classes/sun/tools/attach/HotSpotVirtualMachine.java:201:30:    private static final int ATTACH_ERROR_STARTFAIL     = 102;
# share/classes/sun/tools/attach/HotSpotVirtualMachine.java:204:30:    private static final int ATTACH_ERROR_BADVERSION = 101;
# share/classes/sun/tools/attach/HotSpotVirtualMachine.java:608:32:    private static long defaultAttachTimeout = 10000;
```
