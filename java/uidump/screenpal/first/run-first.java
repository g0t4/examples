#!/usr/bin/env fish

export PATH="$(/usr/libexec/java_home -v 19)/bin:$PATH"

set PID (jps | grep ScreenPal | cut -f1 -d' ')
echo " 
import com.sun.tools.attach.*;
var vm = VirtualMachine.attach(\"$PID\");
vm.loadAgent(\"/Users/wesdemos/repos/github/g0t4/examples/java/uidump/screenpal/demo-agent.jar\",\"hello\");
vm.detach();
" | jshell

# FIND WHERE DOES STDOUT GO?
# lsof -p 98511 | grep log
#    stdin/out/err are all /dev/null
#
# tail /Users/wesdemos/Library/ScreenPal-v3/app-0.log
