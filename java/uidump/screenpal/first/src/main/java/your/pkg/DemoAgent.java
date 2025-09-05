// src/main/java/your/pkg/DemoAgent.java
package your.pkg;

import java.io.*;
import java.lang.instrument.*;
import java.nio.file.*;

public final class DemoAgent {
    public static void agentmain(String args, Instrumentation inst) throws Exception {
        // FYI STDOUT/STDERR map to /dev/null
        System.out.println("Agent v2 attached: " + args); // goes to /Users/wesdemos/Library/ScreenPal-v3/app-0.log
        String tmp = System.getProperty("java.io.tmpdir");
        Path myLog = Path.of(tmp, "fuckyou");
        System.out.println("writing my log to ... " + myLog); // goes to /Users/wesdemos/Library/ScreenPal-v3/app-0.log
        try {
            java.nio.file.Files.writeString(myLog, "FUCKER", StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (Exception e) {
            System.err.println("WRITE FAIL " + e);
        }
    }
}
