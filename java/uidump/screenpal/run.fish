#!/usr/bin/env fish

export PATH="$(/usr/libexec/java_home -v 19)/bin:$PATH"

set PID (jps | grep ScreenPal | cut -f1 -d' ')
set reloader_jar "/Users/wesdemos/repos/github/g0t4/examples/java/uidump/screenpal/dist/reloader.jar"
set agenty_jar "/Users/wesdemos/repos/github/g0t4/examples/java/uidump/screenpal/dist/agenty.jar"
echo " 

import com.sun.tools.attach.*;
var vm = VirtualMachine.attach(\"$PID\");
vm.loadAgent(\"$reloader_jar\",\"impl=$agenty_jar,class=com.agenty.Agenty,action=reload\");
vm.detach();

" | jshell

# lsof -p (jps | grep -i screenpal | head -1 | cut -d' ' -f1)
#    stdin/out/err are all /dev/null
# tail /Users/wesdemos/Library/ScreenPal-v3/app-0.log
#   this is screenpal's log file
