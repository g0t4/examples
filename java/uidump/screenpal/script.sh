javac -d out src/main/java/your/pkg/DemoAgent.java
jar cfm demo-agent.jar META-INF/MANIFEST.MF -C out .
jshell <<'EOF'
import com.sun.tools.attach.*;
var vm = VirtualMachine.attach("<PID>");
vm.loadAgent("demo-agent.jar","hello");
vm.detach();
EOF
