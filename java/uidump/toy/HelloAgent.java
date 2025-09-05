// HelloAgent.java  (NO package)
import java.io.*; import java.lang.instrument.*; import java.nio.file.*;
public class HelloAgent {
  public static void premain(String args, Instrumentation inst) { marker("premain", args); }
  public static void agentmain(String args, Instrumentation inst) { marker("agentmain", args); }
  private static void marker(String where, String args) {
    System.err.println("[SUCK IT BITCHES] " + where);  // see "grep -r SUCK IT" in this repo
    try {
      String pid = java.lang.management.ManagementFactory.getRuntimeMXBean().getName().split("@")[0];
      Files.writeString(Paths.get("agent-ok-" + pid + ".txt"),
        where + " args=" + args + "\n", java.nio.file.StandardOpenOption.CREATE,
        java.nio.file.StandardOpenOption.APPEND);
      System.err.println("[HelloAgent] " + where + " loaded");
    } catch (Throwable t) { t.printStackTrace(); }
  }
}
