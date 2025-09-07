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
    private static volatile Context ctx;

    // ScreenPal Timeline Position Control Automation
    // Use this code in your Java Agent REPL to control timeline position

    // === TIMELINE POSITION CONTROL FUNCTIONS ===

    // Function to click at a specific percentage (0.0 to 1.0) of the timeline
    // Example: clickTimelinePosition(0.25) clicks at 25% through the timeline
    // Example: clickTimelinePosition(0.0) goes to beginning
    // Example: clickTimelinePosition(1.0) goes to end
    public static void clickTimelinePosition(double percentage) {
        try {
            Component timeline = getTimelineComponent();
            if (timeline == null) {
                ctx.log("Timeline component not found!");
                return;
            }

            // Clamp percentage between 0.0 and 1.0
            percentage = Math.max(0.0, Math.min(1.0, percentage));

            int x = (int) (timeline.getWidth() * percentage);
            int y = timeline.getHeight() / 2;
            ctx.log("Clicking timeline at " + x + "," + y);

            java.awt.event.MouseEvent click = new java.awt.event.MouseEvent(
                    timeline,
                    java.awt.event.MouseEvent.MOUSE_CLICKED,
                    System.currentTimeMillis(),
                    0, // no modifiers
                    x,
                    y,
                    1, // single click
                    false // not popup trigger
            );

            timeline.dispatchEvent(click);
            ctx.log("Timeline clicked at " + (percentage * 100) + "% position (" + x + "," + y + ")");

        } catch (Exception e) {
            ctx.log("Error clicking timeline: " + e.toString());
        }
    }

    // Function to get the timeline component reference
    public static Component getTimelineComponent() {
        try {
            Window[] windows = ctx.windows();
            for (Window w : windows) {
                if (!w.isVisible())
                    continue;

                if (w instanceof JFrame) {
                    JFrame frame = (JFrame) w;
                    if (frame.getTitle().contains("ScreenPal")) {
                        // Navigate to timeline: ROOT.0.1.0.4.0.0[3]
                        Container root = frame.getContentPane();
                        JPanel panel0 = (JPanel) root.getComponent(0);
                        JPanel panel1 = (JPanel) panel0.getComponent(1);
                        Container panel10 = (Container) panel1.getComponent(0);
                        JPanel panel104 = (JPanel) panel10.getComponent(4);
                        Container editControls = (Container) panel104.getComponent(0);
                        Container playerControlsPanel = (Container) editControls.getComponent(0);
                        Component timelineComponent = playerControlsPanel.getComponent(3);

                        // Verify this is the correct component
                        if (timelineComponent instanceof JComponent) {
                            JComponent jcomp = (JComponent) timelineComponent;
                            if ("item.editseek".equals(jcomp.getName())) {
                                return timelineComponent;
                            }
                        }
                    }
                }
            }
        } catch (Exception e) {
            ctx.log("Error finding timeline component: " + e.toString());
        }
        return null;
    }

    // Function to get play/pause button (the 48x48 component)
    public static Component getPlayPauseButton() {
        try {
            Component timeline = getTimelineComponent();
            if (timeline != null) {
                Container parent = timeline.getParent();
                // The play button is component [2] - the 48x48 button
                return parent.getComponent(2);
            }
        } catch (Exception e) {
            ctx.log("Error finding play/pause button: " + e.toString());
        }
        return null;
    }

    // Function to click the play/pause button
    public static void clickPlayPause() {
        try {
            Component playButton = getPlayPauseButton();
            if (playButton == null) {
                ctx.log("Play/pause button not found!");
                return;
            }

            java.awt.event.MouseEvent click = new java.awt.event.MouseEvent(
                    playButton,
                    java.awt.event.MouseEvent.MOUSE_CLICKED,
                    System.currentTimeMillis(),
                    0,
                    playButton.getWidth() / 2,
                    playButton.getHeight() / 2,
                    1,
                    false);

            playButton.dispatchEvent(click);
            ctx.log("Play/pause button clicked");

        } catch (Exception e) {
            ctx.log("Error clicking play/pause: " + e.toString());
        }
    }

    // === CONVENIENCE FUNCTIONS ===

    // Jump to specific timeline positions
    public static void jumpToBeginning() {
        clickTimelinePosition(0.0);
    }

    public static void jumpToEnd() {
        clickTimelinePosition(1.0);
    }

    public static void jumpToMiddle() {
        clickTimelinePosition(0.5);
    }

    public static void jumpToQuarter() {
        clickTimelinePosition(0.25);
    }

    public static void jumpToThreeQuarters() {
        clickTimelinePosition(0.75);
    }

    // Example automation sequences
    public static void demonstrateTimelineControl() {
        ctx.log("Starting timeline demonstration...");

        jumpToBeginning();
        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
        }

        jumpToQuarter();
        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
        }

        jumpToMiddle();
        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
        }

        jumpToThreeQuarters();
        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
        }

        jumpToEnd();
        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
        }

        jumpToBeginning();
        ctx.log("Timeline demonstration complete!");
    }

    public static void hardcoded_tests(Context ctx, BufferedWriter out) throws IOException {
        // OUT is not passed to hardcoded, it will only be passed for dynamic code b/c it hooks up to the socket's output stream

        // two purporses for this function:
        // - runs on REPL startup so I can run tests this way

        // === USAGE EXAMPLES ===
        /*
         * To use these functions in your REPL, send commands like:
         * 
         * // Jump to 30% through the timeline clickTimelinePosition(0.3);
         * 
         * // Jump to beginning jumpToBeginning();
         * 
         * // Run the demonstration demonstrateTimelineControl();
         * 
         * // Toggle play/pause clickPlayPause();
         * 
         * // Jump to specific time positions clickTimelinePosition(0.1); // 10% clickTimelinePosition(0.5); // 50% clickTimelinePosition(0.9); // 90%
         */

        ctx.log("ScreenPal Timeline Automation loaded!");
        ctx.log("Available functions:");
        ctx.log("- clickTimelinePosition(percentage)");
        clickTimelinePosition(0.25); // 25%
        ctx.log("- jumpToBeginning(), jumpToEnd(), jumpToMiddle()");
        ctx.log("- clickPlayPause()");
        clickPlayPause();
        ctx.log("- demonstrateTimelineControl()");


        //
        //
        // // - OR, it can be to type in code and then select to send it from nvim over a socket
        //
        // // working ideas, that might be useful:
        //
        // ctx.log("hardcoded 1");
        //
        // // JOptionPane.showMessageDialog(null, "Hello World!", "test", JOptionPane.INFORMATION_MESSAGE);
        //
        // // java 17+ pattern matching (won't work with Janino)
        // for (Window w : ctx.windows()) {
        //     ctx.log("window " + w);
        //     if (w instanceof JFrame f) {
        //         ctx.log("  frame " + f.getTitle());
        //     }
        // }
        // // janino works w/ this:
        // for (Window w : ctx.windows()) {
        //     ctx.log("window " + w);
        //     if (w instanceof javax.swing.JFrame) {
        //         javax.swing.JFrame f = (javax.swing.JFrame) w;
        //         ctx.log("  frame " + f.getTitle());
        //     }
        // }
        //
        // // out.write("here is the data\n");
        // // out.flush();
        //
    }

    public static Object start(java.lang.instrument.Instrumentation inst, String opts) throws Exception {
        ctx = new Context();

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
