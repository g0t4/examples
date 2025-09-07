package com.repl;

import java.lang.instrument.Instrumentation;
import org.codehaus.janino.SimpleCompiler;
import java.awt.*;
import javax.swing.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.function.Consumer;

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

    public static void logComonentAt(Point point, Component base) {

        ctx.log("- getComponentAt: %s".formatted(point));
        // I got these coords myself using my coords mouse tool, s/b play button on left side of timeline
        Component at = base.getComponentAt(point);
        if (at == null) {
            ctx.log("  no component located");
            return;
        }
        ctx.log("found: %s %s".formatted(at.getName(), at.getClass()));
        ctx.log(green("- logComponents():"));
        logComponents(at, 1);
    }

    public static void logComponents(Component c, int level) {
        // if (level > 4) {
        // return;
        // }

        var indent = " ".repeat((level + 1) * 2);
        Consumer<String> logIndented = message -> ctx.log(indent + message);

        // String text = "%s '%s'".formatted(c, c.getClass());
        String text = "%s".formatted(c.toString());
        if (c instanceof JPanel) {
            JPanel p = (JPanel) c;
            logIndented.accept("p #%s '%s' %s".formatted(underline(p.getName()), p.getComponentCount(), text));
            for (Component child : p.getComponents()) {
                logComponents(child, level + 1);
            }
        } else {
            logIndented.accept("c %s".formatted(text));
        }
    }

    // Function to get the timeline component reference
    public static Component getTimelineComponent() {
        try {
            Window[] windows = ctx.windows();
            ctx.log(clearScrollback()); // not essential but helpful!
            ctx.log(bold(red("==============================")));
            for (Window w : windows) {
                if (!w.isVisible())
                    continue;

                if (w instanceof JFrame) {
                    JFrame frame = (JFrame) w;
                    ctx.log("window '%s' name='%s'".formatted(frame.getTitle(), frame.getName()));
                    if (frame.getTitle().contains("ScreenPal")) {

                        ctx.log("  - Claude identified hierarchy()");
                        // Navigate to timeline: ROOT.0.1.0.4.0.0[3]
                        Container root = frame.getContentPane();
                        ctx.log(String.format("  root: '%s'", root.getName()));
                        JPanel panel0 = (JPanel) root.getComponent(0);
                        ctx.log(String.format("    panel0: '%s'", panel0.getName()));
                        JPanel panel1 = (JPanel) panel0.getComponent(1);
                        ctx.log(String.format("      panel1: '%s'", panel1.getName()));
                        Container panel10 = (Container) panel1.getComponent(0);
                        ctx.log(String.format("        panel10: '%s'", panel10.getName()));
                        JPanel panel104 = (JPanel) panel10.getComponent(4);
                        ctx.log(String.format("          panel104: '%s'", panel104.getName()));
                        Container editControls = (Container) panel104.getComponent(0);
                        ctx.log(String.format("            editControls: '%s'", editControls.getName()));
                        Container playerControlsPanel = (Container) editControls.getComponent(0);
                        ctx.log(String.format("              playerControlsPanel: '%s'", playerControlsPanel.getName()));
                        Component timelineComponent = playerControlsPanel.getComponent(3);
                        ctx.log(String.format("                timelineComponent: '%s'", timelineComponent.getName())); // should be "item.editseek"
                        // BINGO claude found what appears to be the control! I confirmed placement on the screen and its right after play and before zoom toggle so yeah that's it!!!

                        ctx.log("- logComponents()");
                        logComponents(root, 0);
                        logComonentAt(new Point(60, 790), w);

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
    // === ADVANCED TIMELINE CONTROL METHODS ===

    // Function to scrub through timeline with drag motion (smooth seeking)
    public void scrubTimeline(double startPercentage, double endPercentage, int durationMs) {
        try {
            Component timeline = getTimelineComponent();
            if (timeline == null) {
                ctx.log("Timeline component not found!");
                return;
            }

            // Clamp percentages
            startPercentage = Math.max(0.0, Math.min(1.0, startPercentage));
            endPercentage = Math.max(0.0, Math.min(1.0, endPercentage));

            int startX = (int) (timeline.getWidth() * startPercentage);
            int endX = (int) (timeline.getWidth() * endPercentage);
            int centerY = timeline.getHeight() / 2;

            // Mouse press at start position
            java.awt.event.MouseEvent press = new java.awt.event.MouseEvent(
                    timeline, java.awt.event.MouseEvent.MOUSE_PRESSED,
                    System.currentTimeMillis(), 0, startX, centerY, 1, false);
            timeline.dispatchEvent(press);

            // Smooth drag motion
            int steps = Math.max(10, durationMs / 50); // At least 10 steps
            long stepDelay = durationMs / steps;

            for (int i = 1; i <= steps; i++) {
                int currentX = startX + ((endX - startX) * i / steps);

                java.awt.event.MouseEvent drag = new java.awt.event.MouseEvent(
                        timeline, java.awt.event.MouseEvent.MOUSE_DRAGGED,
                        System.currentTimeMillis(), 0, currentX, centerY, 1, false);
                timeline.dispatchEvent(drag);

                try {
                    Thread.sleep(stepDelay);
                } catch (InterruptedException e) {
                }
            }

            // Mouse release at end position
            java.awt.event.MouseEvent release = new java.awt.event.MouseEvent(
                    timeline, java.awt.event.MouseEvent.MOUSE_RELEASED,
                    System.currentTimeMillis(), 0, endX, centerY, 1, false);
            timeline.dispatchEvent(release);

            ctx.log("Scrubbed timeline from " + (startPercentage * 100) + "% to " + (endPercentage * 100) + "% over " + durationMs + "ms");

        } catch (Exception e) {
            ctx.log("Error scrubbing timeline: " + e.toString());
        }
    }

    // Function to perform right-click on timeline (might show context menu)
    public void rightClickTimeline(double percentage) {
        try {
            Component timeline = getTimelineComponent();
            if (timeline == null) {
                ctx.log("Timeline component not found!");
                return;
            }

            percentage = Math.max(0.0, Math.min(1.0, percentage));
            int x = (int) (timeline.getWidth() * percentage);
            int y = timeline.getHeight() / 2;

            java.awt.event.MouseEvent rightClick = new java.awt.event.MouseEvent(
                    timeline, java.awt.event.MouseEvent.MOUSE_CLICKED,
                    System.currentTimeMillis(),
                    java.awt.event.InputEvent.BUTTON3_DOWN_MASK,
                    x, y, 1, true // popup trigger
            );
            timeline.dispatchEvent(rightClick);

            ctx.log("Right-clicked timeline at " + (percentage * 100) + "% position");

        } catch (Exception e) {
            ctx.log("Error right-clicking timeline: " + e.toString());
        }
    }

    // Function to double-click timeline (might have special behavior)
    public void doubleClickTimeline(double percentage) {
        try {
            Component timeline = getTimelineComponent();
            if (timeline == null) {
                ctx.log("Timeline component not found!");
                return;
            }

            percentage = Math.max(0.0, Math.min(1.0, percentage));
            int x = (int) (timeline.getWidth() * percentage);
            int y = timeline.getHeight() / 2;

            java.awt.event.MouseEvent doubleClick = new java.awt.event.MouseEvent(
                    timeline, java.awt.event.MouseEvent.MOUSE_CLICKED,
                    System.currentTimeMillis(), 0, x, y, 2, false // click count = 2
            );
            timeline.dispatchEvent(doubleClick);

            ctx.log("Double-clicked timeline at " + (percentage * 100) + "% position");

        } catch (Exception e) {
            ctx.log("Error double-clicking timeline: " + e.toString());
        }
    }

    // Function to send arrow key navigation (if timeline has focus)
    public void sendArrowKey(String direction) {
        try {
            Component timeline = getTimelineComponent();
            if (timeline == null) {
                ctx.log("Timeline component not found!");
                return;
            }

            JComponent jcomp = (JComponent) timeline;

            // Try to focus the timeline first
            boolean focused = jcomp.requestFocusInWindow();
            if (!focused) {
                ctx.log("Could not focus timeline component");
                return;
            }

            int keyCode;
            switch (direction.toLowerCase()) {
            case "left":
                keyCode = java.awt.event.KeyEvent.VK_LEFT;
                break;
            case "right":
                keyCode = java.awt.event.KeyEvent.VK_RIGHT;
                break;
            case "up":
                keyCode = java.awt.event.KeyEvent.VK_UP;
                break;
            case "down":
                keyCode = java.awt.event.KeyEvent.VK_DOWN;
                break;
            default:
                ctx.log("Invalid direction: " + direction + ". Use: left, right, up, down");
                return;
            }

            java.awt.event.KeyEvent keyEvent = new java.awt.event.KeyEvent(
                    jcomp, java.awt.event.KeyEvent.KEY_PRESSED,
                    System.currentTimeMillis(), 0, keyCode, java.awt.event.KeyEvent.CHAR_UNDEFINED);
            jcomp.dispatchEvent(keyEvent);

            ctx.log("Sent " + direction + " arrow key to timeline");

        } catch (Exception e) {
            ctx.log("Error sending arrow key: " + e.toString());
        }
    }

    // === ENHANCED CONVENIENCE FUNCTIONS ===

    // Smooth scrubbing demonstrations
    public void scrubForward() {
        scrubTimeline(0.0, 1.0, 2000);
    } // 2 second scrub to end

    public void scrubBackward() {
        scrubTimeline(1.0, 0.0, 2000);
    } // 2 second scrub to start

    public void scrubSection() {
        scrubTimeline(0.2, 0.8, 1500);
    } // Scrub middle section

    // Fine navigation with arrow keys
    public void stepForward() {
        sendArrowKey("right");
    }

    public void stepBackward() {
        sendArrowKey("left");
    }

    // Context menu exploration
    public void exploreContextMenu() {
        rightClickTimeline(0.5);
        ctx.log("Check for context menu at timeline center");
    }

    // === TIMELINE ANALYSIS FUNCTIONS ===

    // Get timeline dimensions and position info
    public void analyzeTimeline() {
        try {
            Component timeline = getTimelineComponent();
            if (timeline == null) {
                ctx.log("Timeline component not found!");
                return;
            }

            ctx.log("=== TIMELINE ANALYSIS ===");
            ctx.log("Class: " + timeline.getClass().getName());
            ctx.log("Name: " + ((JComponent) timeline).getName());
            ctx.log("Size: " + timeline.getWidth() + "x" + timeline.getHeight() + " pixels");
            ctx.log("Location on screen: " + timeline.getLocationOnScreen());
            ctx.log("Pixel width: " + timeline.getWidth() + " pixels = 100% timeline");
            ctx.log("1% = " + (timeline.getWidth() / 100.0) + " pixels");
            ctx.log("Focusable: " + timeline.isFocusable());
            ctx.log("Has focus: " + ((JComponent) timeline).hasFocus());

            // Count event listeners
            JComponent jcomp = (JComponent) timeline;
            ctx.log("Mouse listeners: " + jcomp.getMouseListeners().length);
            ctx.log("Mouse motion listeners: " + jcomp.getMouseMotionListeners().length);
            ctx.log("Key listeners: " + jcomp.getKeyListeners().length);

        } catch (Exception e) {
            ctx.log("Error analyzing timeline: " + e.toString());
        }
    }

    // === USAGE EXAMPLES ===
    /*
     * BASIC USAGE: clickTimelinePosition(0.3); // Jump to 30% scrubTimeline(0.1, 0.9, 3000); // Smooth 3-second scrub from 10% to 90%
     * 
     * ADVANCED INTERACTION: rightClickTimeline(0.5); // Right-click at center (context menu?) doubleClickTimeline(0.25); // Double-click at 25% (special action?) stepForward(); // Fine navigation with arrow key
     * 
     * DEMONSTRATIONS: scrubForward(); // Smooth scrub to end scrubBackward(); // Smooth scrub to start demonstrateTimelineControl(); // Full demo sequence
     * 
     * ANALYSIS: analyzeTimeline(); // Get detailed timeline info
     */

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

        // ctx.log("ScreenPal Timeline Automation loaded!");
        // ctx.log("Available functions:");
        // ctx.log("- clickTimelinePosition(percentage)");
        // // clickTimelinePosition(0.25); // 25%
        // ctx.log("- jumpToBeginning(), jumpToEnd(), jumpToMiddle()");
        // ctx.log("- clickPlayPause()");
        // // clickPlayPause();
        // ctx.log("- demonstrateTimelineControl()");
        // demonstrateTimelineControl();
        ctx.log("- wes");
        getTimelineComponent();

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
        // ctx.log("window " + w);
        // if (w instanceof JFrame f) {
        // ctx.log(" frame " + f.getTitle());
        // }
        // }
        // // janino works w/ this:
        // for (Window w : ctx.windows()) {
        // ctx.log("window " + w);
        // if (w instanceof javax.swing.JFrame) {
        // javax.swing.JFrame f = (javax.swing.JFrame) w;
        // ctx.log(" frame " + f.getTitle());
        // }
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

    public static String bold(String msg) {
        return "\u001B[1m" + msg + "\u001B[0m";
    }

    public static String green(String msg) {
        return "\u001B[32m" + msg + "\u001B[0m";
    }

    public static String red(String msg) {
        return "\u001B[31m" + msg + "\u001B[0m";
    }

    public static String yellow(String msg) {
        return "\u001B[33m" + msg + "\u001B[0m";
    }

    public static String blue(String msg) {
        return "\u001B[34m" + msg + "\u001B[0m";
    }

    public static String cyan(String msg) {
        return "\u001B[36m" + msg + "\u001B[0m";
    }

    public static String magenta(String msg) {
        return "\u001B[35m" + msg + "\u001B[0m";
    }

    public static String white(String msg) {
        return "\u001B[37m" + msg + "\u001B[0m";
    }

    public static String black(String msg) {
        return "\u001B[30m" + msg + "\u001B[0m";
    }

    public static String underline(String msg) {
        return "\u001B[4m" + msg + "\u001B[0m";
    }

    public static String italic(String msg) {
        return "\u001B[3m" + msg + "\u001B[0m";
    }

    public static String bgRed(String msg) {
        return "\u001B[41m" + msg + "\u001B[0m";
    }

    public static String bgGreen(String msg) {
        return "\u001B[42m" + msg + "\u001B[0m";
    }

    public static String bgYellow(String msg) {
        return "\u001B[43m" + msg + "\u001B[0m";
    }

    public static String bgBlue(String msg) {
        return "\u001B[44m" + msg + "\u001B[0m";
    }

    public static String bgMagenta(String msg) {
        return "\u001B[45m" + msg + "\u001B[0m";
    }

    public static String bgCyan(String msg) {
        return "\u001B[46m" + msg + "\u001B[0m";
    }

    public static String bgWhite(String msg) {
        return "\u001B[47m" + msg + "\u001B[0m";
    }

    public static String bgBlack(String msg) {
        return "\u001B[40m" + msg + "\u001B[0m";
    }

    public static String clearScrollback() {
        return "\u001B]1337;ClearScrollback\u0007\u001B[0m";
    }

}
