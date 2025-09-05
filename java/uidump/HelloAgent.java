// HelloAgent.java  (Manifest: Agent-Class: HelloAgent)
import java.io.*; import java.lang.instrument.*; import java.nio.file.*; 
public class HelloAgent {
  public static void agentmain(String args, Instrumentation inst) {
    try {
      String pid = java.lang.management.ManagementFactory.getRuntimeMXBean().getName().split("@")[0];
      Files.writeString(Paths.get("/tmp/agent-ok-" + pid + ".txt"),
        "hello from agent; args=" + args + "\n");
    } catch (Throwable t) {
      try { Files.writeString(Paths.get("/tmp/agent-err.txt"), t.toString()); } catch (Exception ignored) {}
      throw new RuntimeException(t);
    }
  }
}
