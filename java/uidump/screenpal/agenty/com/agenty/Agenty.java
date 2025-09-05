package com.agenty;

import java.io.PrintStream;
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.accessibility.*;

public final class Agenty {
    // private static volatile ClassFileTransformer transformer;

    public static Object start(java.lang.instrument.Instrumentation inst, String opts) {
        Runnable r = () -> {
            System.out.println("[agenty] start-04=");
            for (Window w : Window.getWindows())
                if (w.isDisplayable())
                    dump(w, 0);
            Window active = KeyboardFocusManager.getCurrentKeyboardFocusManager().getActiveWindow();
            System.out.println("[agenty] active=" + (active == null ? "null" : active.getClass().getName()));
        };
        if (SwingUtilities.isEventDispatchThread())
            r.run();
        else
            try {
                EventQueue.invokeAndWait(r);
            } catch (Exception e) {
                e.printStackTrace();
            }
        return (AutoCloseable) () -> {
        };
    }

    private static void dump(Component c, int depth) {
        String pad = "  ".repeat(depth);
        String title = (c instanceof Frame f) ? f.getTitle() : (c instanceof Dialog d) ? d.getTitle() : null;
        System.out.printf("JERKWAD '%s'", title);
        if (title != null && title.contains("ScreenPal - 3.19.4")) {
            // FYI original title "\nScreenPal - 3.19.4\n" had new lines (or smth off)
            // before and after it! so use contains
            System.out.println("FOUND YOU FUUUER");
            if (c instanceof Frame f) {
                System.out.println("  fuuuu is a frame");
                f.setTitle("FUUUU FRAME");
            }

            if (c instanceof Dialog d) {
                System.out.println("  fuuuu is a dialog");
                d.setTitle("FUUUU DIALOG");
            }
        }

        var ac = (c instanceof Accessible a) ? a.getAccessibleContext() : null;
        System.out.printf("[agenty]%s%s bounds=%s visible=%s name=%s accName=%s%n",
                pad, c.getClass().getName(), c.getBounds(), c.isVisible(),
                (c.getName()), ac != null ? ac.getAccessibleName() : null);
        if (title != null)
            System.out.printf("[agenty]%s  title=%s%n", pad, title);
        if (c instanceof Container ct)
            for (Component child : ct.getComponents())
                dump(child, depth + 1);
    }

}
