package com.agent.repl;

import java.lang.instrument.Instrumentation;
import org.codehaus.janino.SimpleCompiler;
import java.awt.*;
import javax.swing.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;

public final class AgentEntry {
    interface Action {
        void run(Context ctx) throws Exception;
    }

    public static final class Context {
        public void onEdt(Runnable r) {
            if (SwingUtilities.isEventDispatchThread())
                r.run();
            else
                try {
                    EventQueue.invokeAndWait(r);
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
        }

        public Window[] windows() {
            return Window.getWindows();
        }

        public void log(String s) {
            System.out.println("[repl] " + s);
        }
    }

    private static volatile ServerSocket server;
    private static volatile Thread thread;

    public static Object start(java.lang.instrument.Instrumentation inst, String opts) throws Exception {
        server = new ServerSocket(0, 0, InetAddress.getLoopbackAddress());
        String token = java.util.UUID.randomUUID().toString();
        System.out.println("[repl] listening on 127.0.0.1:" + server.getLocalPort() + " token=" + token);

        Context ctx = new Context();
        thread = new Thread(() -> {
            final ServerSocket srv = server; // effectively final capture
            final String tok = token;
            while (!Thread.currentThread().isInterrupted()) {
                try (Socket s = server.accept();
                        BufferedReader in = new BufferedReader(
                                new InputStreamReader(s.getInputStream(), StandardCharsets.UTF_8));
                        BufferedWriter out = new BufferedWriter(
                                new OutputStreamWriter(s.getOutputStream(), StandardCharsets.UTF_8))) {

                    if (!token.equals(in.readLine())) {
                        out.write("ERR bad token\n");
                        out.flush();
                        continue;
                    }
                    StringBuilder body = new StringBuilder();
                    for (String line; (line = in.readLine()) != null && !line.equals(".");)
                        body.append(line).append('\n');

                    String src = """
                            import java.awt.*; import javax.swing.*;
                            public class UserCode implements %s.Action {
                              public void run(%s.Context ctx) throws Exception {
                                %s
                              }
                            }
                            """.formatted(AgentEntry.class.getName(), AgentEntry.class.getName(), body);

                    try {
                        SimpleCompiler c = new SimpleCompiler();
                        c.setParentClassLoader(AgentEntry.class.getClassLoader());
                        c.cook(src);
                        Class<?> k = c.getClassLoader().loadClass("UserCode");
                        Action a = (Action) k.getDeclaredConstructor().newInstance();
                        ctx.onEdt(() -> {
                            try {
                                a.run(ctx);
                            } catch (Exception e) {
                                throw new RuntimeException(e);
                            }
                        });
                        out.write("OK\n");
                        out.flush();
                    } catch (Throwable t) {
                        out.write(("ERR " + t + "\n"));
                        out.flush();
                    }
                } catch (IOException ignore) {
                    /* next */ }
            }
        }, "repl-server");
        thread.setDaemon(true);
        thread.start();

        return (AutoCloseable) () -> {
            thread.interrupt();
            try {
                server.close();
            } catch (IOException ignored) {
            }
        };
    }
}
