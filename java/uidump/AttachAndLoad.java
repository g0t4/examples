// File: AttachAndLoad.java
// Usage: java AttachAndLoad <pid> </absolute/path/to/agent.jar> [agent-args]
import com.sun.tools.attach.VirtualMachine;
public class AttachAndLoad {
  public static void main(String[] args) throws Exception {
    if (args.length < 2) {
      System.err.println("Usage: java AttachAndLoad <pid> </abs/path/agent.jar> [args]");
      System.exit(1);
    }
    String pid = args[0];
    String jar = args[1];
    String a = args.length > 2 ? args[2] : "";
    VirtualMachine vm = VirtualMachine.attach(pid);
    vm.loadAgent(jar, a);
    vm.detach();
    System.out.println("Loaded agent into " + pid + ". Check ui-dump-" + pid + ".txt");
  }
}
