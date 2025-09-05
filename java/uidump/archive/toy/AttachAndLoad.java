// AttachAndLoad.java
import com.sun.tools.attach.VirtualMachine;
public class AttachAndLoad {
  public static void main(String[] a) throws Exception {
    String pid = a[0], jar = a[1], args = a.length>2 ? a[2] : "";
    var vm = VirtualMachine.attach(pid);
    vm.loadAgent(jar, args);
    vm.detach();
    System.out.println("Loaded agent into " + pid);
  }
}
