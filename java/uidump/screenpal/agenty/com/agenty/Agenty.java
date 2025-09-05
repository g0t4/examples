package com.agenty;

import java.io.PrintStream;
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.accessibility.*;
import java.util.*;
import java.util.function.*;
import javax.swing.text.*;

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

        onEdt(() -> find(c -> true).forEach(c -> System.out.printf("[stalker] %s name=%s acc=%s text=%s%n",
                c.getClass().getName(), c.getName(), accName(c),
                (c instanceof AbstractButton b ? b.getText() : c instanceof JTextComponent t ? t.getText() : null))));

        return (AutoCloseable) () -> {
        };

    }

    // TODO use this onEdt to make changes and use the helpers below too to find
    // controls
    static void onEdt(Runnable r) {
        if (SwingUtilities.isEventDispatchThread())
            r.run();
        else
            EventQueue.invokeLater(r);
    }

    static ArrayList<Component> find(Predicate<Component> test) {
        ArrayList<Component> out = new ArrayList<>();
        for (Window w : Window.getWindows())
            walk(w, test, out);
        return out;
    }

    static void walk(Component c, Predicate<Component> test, ArrayList<Component> out) {
        if (test.test(c))
            out.add(c);
        if (c instanceof Container k)
            for (Component ch : k.getComponents()) {
                AccessibleContext context = ch.getAccessibleContext();
                if (context != null) {
                    AccessibleValue ax_value = ch.getAccessibleContext().getAccessibleValue();
                    if (ax_value != null) {
                        System.out.printf("ax_value %s", ax_value);
                        System.out.printf("ax_value.toString() %s", ax_value.toString());
                    }
                }
                walk(ch, test, out);
            }
    }

    static String accName(Component c) {
        return (c instanceof Accessible a && a.getAccessibleContext() != null)
                ? a.getAccessibleContext().getAccessibleName()
                : null;
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
