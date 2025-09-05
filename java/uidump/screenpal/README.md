## VisualVM heapdumps

- Can see images loaded: 
    - `com.screencastomatic.common.bW#6 : 1,600x1,066` => show preview panel
- TODO!! explore a bit more and makes sure you can find meaningful data to use before pursuing same data via jcmd (below) or agent (below)

## jcmd

WHAT all can I find with this command? if it works to get stuff I can run right in hammerspoon lua code!
  classes show up => 
    ./jattach $PID jcmd VM.classes | grep -i editorframe

## jdk troubleshooting

use checkout in: github/openjdk/jdk/src/jdk.attach

## own agent (see java code in this dir)

TODO TEST IT
