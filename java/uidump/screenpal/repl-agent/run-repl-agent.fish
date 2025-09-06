#!/usr/bin/env fish

export PATH="$(/usr/libexec/java_home -v 19)/bin:$PATH"

set PID (jps | grep ScreenPal | cut -f1 -d' ')
set reloader_jar "$HOME/repos/github/g0t4/examples/java/uidump/screenpal/dist/reloader.jar"
set repl_jar "$HOME/repos/github/g0t4/examples/java/uidump/screenpal/repl-agent/target/repl-agent-1.0-SNAPSHOT-all.jar"
if not test -f $reloader_jar
    echo MISSING RELOADER AGENT:
    echo "  $reloader_jar"
    return
end
if not test -f $repl_jar
    echo MISSING REPL AGENT:
    echo "  $repl_jar"
    return
end
echo " 

import com.sun.tools.attach.*;
var vm = VirtualMachine.attach(\"$PID\");
vm.loadAgent(\"$reloader_jar\",\"impl=$repl_jar,class=com.repl.Agent,action=reload\");
vm.detach();

" | jshell

# lsof -p (jps | grep -i screenpal | head -1 | cut -d' ' -f1)
#    stdin/out/err are all /dev/null
