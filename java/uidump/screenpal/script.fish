#!/usr/bin/env fish

export PATH="$(/usr/libexec/java_home -v 19)/bin:$PATH"

javac -d out src/main/java/your/pkg/DemoAgent.java
jar cfm demo-agent.jar META-INF/MANIFEST.MF -C out .
set PID (jps | grep ScreenPal | cut -f1 -d' ')
echo " 
import com.sun.tools.attach.*;
var vm = VirtualMachine.attach(\"$PID\");
vm.loadAgent(\"demo-agent.jar\",\"hello\");
vm.detach();
" | jshell
