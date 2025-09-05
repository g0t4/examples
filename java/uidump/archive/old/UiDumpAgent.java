// File: UiDumpAgent.java
// Compile with JDK 11+ (also works on newer). No extra deps.
// Manifest needs: Agent-Class: UiDumpAgent
import java.awt.*;
import java.awt.event.*;
import java.io.*;
import java.lang.instrument.Instrumentation;
import java.lang.reflect.Method;
import java.nio.file.*;
import java.util.*;
import java.util.List;
import java.util.concurrent.CountDownLatch;

public class UiDumpAgent {
  public static void agentmain(String args, Instrumentation inst) {
    new Thread(() -> {
      try {
        String pid = java.lang.management.ManagementFactory.getRuntimeMXBean().getName().split("@")[0];
        Path out = Paths.get("ui-dump-" + pid + ".txt");
        try (BufferedWriter w = Files.newBufferedWriter(out)) {
          w.write("=== Swing (AWT) ===\n");
          dumpSwing(w);
          w.write("\n=== JavaFX ===\n");
          dumpJavaFX(w);
        }
      } catch (Throwable t) {
        t.printStackTrace();
      }
    }, "UiDumpAgent-Worker").start();
  }

  private static void dumpSwing(BufferedWriter w) throws Exception {
    for (Frame f : Frame.getFrames()) {
      if (!f.isDisplayable()) continue;
      writeCompTree(w, f, 0, new HashSet<>());
    }
  }

  private static void writeCompTree(BufferedWriter w, Component c, int depth, Set<Component> seen) throws Exception {
    if (c == null || seen.contains(c)) return;
    seen.add(c);
    String indent = "  ".repeat(depth);
    Rectangle b = c.getBounds();
    String name = c.getName();
    String cls = c.getClass().getName();
    String text = trySwingText(c);
    w.write(String.format("%s%s name=%s bounds=%s text=%s%n",
            indent, cls, name, b, text));
    if (c instanceof Container) {
      for (Component child : ((Container) c).getComponents()) {
        writeCompTree(w, child, depth + 1, seen);
      }
    }
  }

  private static String trySwingText(Component c) {
    try {
      // Common Swing text holders: AbstractButton, JLabel, JTextComponent, JEditorPane
      for (String m : List.of("getText", "getTitle", "getToolTipText")) {
        Method mm = c.getClass().getMethod(m);
        mm.setAccessible(true);
        Object v = mm.invoke(c);
        if (v != null && !String.valueOf(v).isBlank()) return sanitize(String.valueOf(v));
      }
    } catch (Throwable ignored) {}
    return "";
  }

  private static String sanitize(String s) {
    return s.replace("\n", "\\n").replace("\r", "");
  }

  // -------- JavaFX --------
  private static void dumpJavaFX(BufferedWriter w) throws Exception {
    try {
      Class<?> platform = Class.forName("javafx.application.Platform");
      Method isFxAppThread = platform.getMethod("isFxApplicationThread");
      Method runLater = platform.getMethod("runLater", Runnable.class);

      Runnable task = () -> {
        try {
          Class<?> windowCls = Class.forName("javafx.stage.Window");
          Method getWindows = windowCls.getMethod("getWindows");
          @SuppressWarnings("unchecked")
          List<Object> windows = (List<Object>) getWindows.invoke(null);
          for (Object win : windows) {
            Method getScene = win.getClass().getMethod("getScene");
            Object scene = getScene.invoke(win);
            if (scene == null) continue;
            Object root = scene.getClass().getMethod("getRoot").invoke(scene);
            writeFxNode(w, root, 0, new HashSet<>());
          }
        } catch (Throwable t) {
          try { w.write("JavaFX error: " + t + "\n"); } catch (IOException ignored) {}
        }
      };

      if ((boolean) isFxAppThread.invoke(null)) {
        task.run();
      } else {
        CountDownLatch latch = new CountDownLatch(1);
        runLater.invoke(null, (Runnable) () -> { task.run(); latch.countDown(); });
        latch.await();
      }
    } catch (ClassNotFoundException e) {
      w.write("JavaFX not present on classpath.\n");
    }
  }

  private static void writeFxNode(BufferedWriter w, Object node, int depth, Set<Object> seen) throws Exception {
    if (node == null || seen.contains(node)) return;
    seen.add(node);
    String indent = "  ".repeat(depth);
    Class<?> nodeCls = node.getClass();
    String cls = nodeCls.getName();

    String id = "";
    try {
      Object v = nodeCls.getMethod("getId").invoke(node);
      id = String.valueOf(v);
    } catch (Throwable ignored) {}

    String text = "";
    try {
      // Labeled, TextInputControl, WebView HTML
      if (hasMethod(nodeCls, "getText")) {
        Object v = nodeCls.getMethod("getText").invoke(node);
        if (v != null) text = sanitize(String.valueOf(v));
      }
      if (cls.equals("javafx.scene.web.WebView")) {
        Object engine = nodeCls.getMethod("getEngine").invoke(node);
        Object html = engine.getClass()
                .getMethod("executeScript", String.class)
                .invoke(engine, "document.documentElement.outerHTML");
        if (html != null) {
          text = "[HTML length=" + String.valueOf(html).length() + "]";
          // Optionally write full HTML:
          w.write(indent + "javafx.scene.web.WebView HTML >>>\n");
          w.write(String.valueOf(html));
          w.write("\n" + indent + "<<< END HTML\n");
        }
      }
    } catch (Throwable ignored) {}

    w.write(String.format("%s%s id=%s text=%s%n", indent, cls, id, text));

    // Traverse children if it's a Parent
    try {
      Class<?> parentCls = Class.forName("javafx.scene.Parent");
      if (parentCls.isInstance(node)) {
        @SuppressWarnings("unchecked")
        List<Object> kids = (List<Object>) nodeCls.getMethod("getChildrenUnmodifiable").invoke(node);
        for (Object child : kids) writeFxNode(w, child, depth + 1, seen);
      }
    } catch (Throwable ignored) {}
  }

  private static boolean hasMethod(Class<?> c, String name) {
    for (Method m : c.getMethods()) if (m.getName().equals(name)) return true;
    return false;
  }
}
