## VisualVM heapdumps

- Can see images loaded: 
    - `com.screencastomatic.common.bW#6 : 1,600x1,066` => show preview panel

## jcmd

WHAT all can I find with this command? if it works to get stuff I can run right in hammerspoon lua code!
  classes show up => 
    ./jattach $PID jcmd VM.classes | grep -i editorframe

## jdk troubleshooting

use checkout in: github/openjdk/jdk/src/jdk.attach
