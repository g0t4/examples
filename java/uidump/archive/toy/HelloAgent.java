// HelloAgent.java  (NO package)
import java.io.*; import java.lang.instrument.*; import java.nio.file.*;
public class HelloAgent {
    public static void agentmain(String args, Instrumentation inst) {
        String pid = java.lang.management.ManagementFactory.getRuntimeMXBean().getName().split("@")[0];
        String tmp = System.getProperty("java.io.tmpdir");
        log(tmp + "agent-ok-"+pid+".txt", "ok");
        System.err.println("[HelloAgent] loaded pid=" + pid + " tmp=" + tmp);
    }
    static void log(String p, String s){
        try { java.nio.file.Files.writeString(java.nio.file.Path.of(p), s+"\n",
            java.nio.file.StandardOpenOption.CREATE, java.nio.file.StandardOpenOption.APPEND); }
        catch(Exception e){ System.err.println("WRITE FAIL "+p+": "+e); }
    }

    public static void premain(String args, Instrumentation inst) { 
        System.err.println("[HelloAgent] premain");
    }
}
