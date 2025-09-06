package com.repl;

import java.lang.instrument.Instrumentation;
import org.codehaus.janino.SimpleCompiler;
import java.awt.*;
import javax.swing.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;

public final class Agent {
    public interface Action {
        void run(Context ctx, BufferedWriter out) throws Exception;
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

    public static void hardcoded_tests(Context ctx, BufferedWriter out) throws IOException {
        // OUT is not passed to hardcoded, it will only be passed for dynamic code b/c it hooks up to the socket's output stream

        // two purporses for this function:
        // - runs on REPL startup so I can run tests this way
        // - OR, it can be to type in code and then select to send it from nvim over a socket

        // working ideas, that might be useful:

        ctx.log("hardcoded 1");

        // JOptionPane.showMessageDialog(null, "Hello World!", "test", JOptionPane.INFORMATION_MESSAGE);

        // java 17+ pattern matching (won't work with Janino)
        for (Window w : ctx.windows()) {
            ctx.log("window " + w);
            if (w instanceof JFrame f) {
                ctx.log("  frame " + f.getTitle());
            }
        }
        // janino works w/ this:
        for (Window w : ctx.windows()) {
            ctx.log("window " + w);
            if (w instanceof javax.swing.JFrame) {
                javax.swing.JFrame f = (javax.swing.JFrame) w;
                ctx.log("  frame " + f.getTitle());
            }
        }

        // out.write("here is the data\n");
        // out.flush();

    }

    public static Object start(java.lang.instrument.Instrumentation inst, String opts) throws Exception {
        Context ctx = new Context();
        try {
            hardcoded_tests(ctx, null);
        } catch (Throwable t) {
            ctx.log("hardcoded test failed: " + t);
        }

        // * start server to accept code over a socket
        server = new ServerSocket(8200, 0, InetAddress.getLoopbackAddress());
        // String token = java.util.UUID.randomUUID().toString();
        // System.out.println("[repl] listening on 127.0.0.1:" + server.getLocalPort() + " token=" + token);
        System.out.println("[repl] listening on 127.0.0.1:" + server.getLocalPort());

        thread = new Thread(() -> {

            final ServerSocket srv = server; // effectively final capture
            // final String tok = token;
            while (!Thread.currentThread().isInterrupted()) {
                try (Socket s = srv.accept();
                        BufferedReader in = new BufferedReader(
                                new InputStreamReader(s.getInputStream(), StandardCharsets.UTF_8));
                        BufferedWriter out = new BufferedWriter(
                                new OutputStreamWriter(s.getOutputStream(), StandardCharsets.UTF_8))) {

                    // if (!tok.equals(in.readLine())) {
                    // out.write("ERR bad token\n");
                    // out.flush();
                    // continue;
                    // }
                    StringBuilder body = new StringBuilder();
                    for (String line; (line = in.readLine()) != null && !line.equals(".");)
                        body.append(line).append('\n');

                    String src = """
                            import java.awt.*; import javax.swing.*;
                            import java.io.*;
                            public class UserCode implements %s.Action {
                              public void run(%s.Context ctx, BufferedWriter out) throws Exception {
                                try {
                                  %s
                                }
                                catch (Throwable t) {
                                  ctx.log("[repl][ERR] check next message"); // separate just in case toString() fails
                                  ctx.log("[repl][ERR]\\n" + t.toString());
                                }
                              }
                            }
                            """.formatted(Agent.class.getName(), Agent.class.getName(), body);
                    try {
                        SimpleCompiler c = new SimpleCompiler();
                        c.setParentClassLoader(Agent.class.getClassLoader());
                        c.cook(src);
                        Class<?> k = c.getClassLoader().loadClass("UserCode");
                        Action a = (Action) k.getDeclaredConstructor().newInstance();
                        ctx.onEdt(() -> {
                            try {
                                a.run(ctx, out);
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
