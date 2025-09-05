// src/main/java/your/pkg/DemoAgent.java
package your.pkg;
import java.lang.instrument.Instrumentation;
public final class DemoAgent {
    public static void agentmain(String args, Instrumentation inst) throws Exception {
        System.out.println("Agent attached: " + args);
    }
}
