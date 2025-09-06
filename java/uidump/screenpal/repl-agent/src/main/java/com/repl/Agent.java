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

    public static void hardcoded_tests(Context ctx) {
        // TODO setup nvim action to send selection to socket! so I can type it in IDE and send at push of button
        //  OR I can compile again and run it that way! either way put all the code here:

        // working ideas, that might be useful:
        // ctx.log("hardcoded 1");
        // JOptionPane.showMessageDialog(null, "Hello World!", "test", JOptionPane.INFORMATION_MESSAGE);


    }

    public static Object start(java.lang.instrument.Instrumentation inst, String opts) throws Exception {
        Context ctx = new Context();
        hardcoded_tests(ctx);

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
                            public class UserCode implements %s.Action {
                              public void run(%s.Context ctx) throws Exception {
                                %s
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
