// UiDumpAgent2.java  (Manifest: Agent-Class: UiDumpAgent2)
import java.io.*; import java.lang.instrument.*; import java.nio.file.*; import java.util.*;
public class UiDumpAgent2 {
  public static void agentmain(String args, Instrumentation inst) {
    try {
      new Thread(() -> { try { run(); } catch (Throwable t) { log("FATAL " + t); } },
                 "UiDumpAgent2").start();
    } catch (Throwable t) {
      log("INIT " + t); throw new RuntimeException(t);
    }
  }
  private static void run() throws Exception {
    String pid = java.lang.management.ManagementFactory.getRuntimeMXBean().getName().split("@")[0];
    Path out = Path.of("/tmp/ui-dump-" + pid + ".txt"); logPath = Path.of("/tmp/ui-dump-" + pid + ".log");
    try (BufferedWriter w = Files.newBufferedWriter(out)) {
      dumpSwingReflect(w);
      dumpJavaFXReflect(w);
    }
  }
  private static Path logPath;
  private static void log(String s){ try{ Files.writeString(logPath!=null?logPath:Path.of("/tmp/ui-dump.log"), s+"\n"); }catch(Exception ignored){} }

  // ---- Swing via reflection (avoids linking java.desktop at load) ----
  @SuppressWarnings("unchecked")
  private static void dumpSwingReflect(BufferedWriter w) {
    try {
      Class<?> frameCls = Class.forName("java.awt.Frame");
      Object frames = frameCls.getMethod("getFrames").invoke(null);
      w.write("=== Swing (reflect) ===\n");
      for (Object f : (Object[]) frames) writeCompTreeReflect(w, f, 0, new HashSet<>());
    } catch (Throwable t) { log("SWING " + t); }
  }
  private static void writeCompTreeReflect(BufferedWriter w, Object comp, int d, Set<Object> seen) throws Exception {
    if (comp==null || seen.contains(comp)) return; seen.add(comp);
    String indent = "  ".repeat(d);
    Class<?> c = comp.getClass();
    String cls = c.getName();
    String name = tryStr(() -> c.getMethod("getName").invoke(comp));
    String bounds = tryStr(() -> String.valueOf(c.getMethod("getBounds").invoke(comp)));
    String text = tryTextReflect(comp, c);
    w.write(String.format("%s%s name=%s bounds=%s text=%s%n", indent, cls, name, bounds, text));
    // If it's a Container, iterate children
    try {
      Class<?> container = Class.forName("java.awt.Container");
      if (container.isInstance(comp)) {
        Object kids = c.getMethod("getComponents").invoke(comp);
        for (Object child : (Object[]) kids) writeCompTreeReflect(w, child, d+1, seen);
      }
    } catch (Throwable ignored) {}
  }
  private static String tryTextReflect(Object comp, Class<?> c) {
    for (String m : new String[]{"getText","getTitle","getToolTipText"}) {
      try { Object v = c.getMethod(m).invoke(comp); if (v!=null && !v.toString().isBlank()) return v.toString(); } catch(Throwable ignored){}
    }
    return "";
  }

  // ---- JavaFX via reflection ----
  @SuppressWarnings("unchecked")
  private static void dumpJavaFXReflect(BufferedWriter w) {
    try {
      w.write("\n=== JavaFX (reflect) ===\n");
      Class<?> platform = Class.forName("javafx.application.Platform");
      boolean onFx = (boolean) platform.getMethod("isFxApplicationThread").invoke(null);
      Runnable r = () -> {
        try {
          Class<?> winCls = Class.forName("javafx.stage.Window");
          java.util.List<Object> wins = (java.util.List<Object>) winCls.getMethod("getWindows").invoke(null);
          for (Object win : wins) {
            Object scene = win.getClass().getMethod("getScene").invoke(win);
            if (scene == null) continue;
            Object root = scene.getClass().getMethod("getRoot").invoke(scene);
            writeFxNodeReflect(w, root, 0, new HashSet<>());
          }
        } catch (Throwable t) { log("JFX-RUN " + t); }
      };
      if (onFx) r.run(); else {
        java.util.concurrent.CountDownLatch latch = new java.util.concurrent.CountDownLatch(1);
        platform.getMethod("runLater", Runnable.class).invoke(null, (Runnable) ()->{ r.run(); latch.countDown(); });
        latch.await();
      }
    } catch (ClassNotFoundException e) {
      try { w.write("JavaFX not present.\n"); } catch (IOException ignored) {}
    } catch (Throwable t) { log("JFX " + t); }
  }
  private static void writeFxNodeReflect(BufferedWriter w, Object node, int d, Set<Object> seen) throws Exception {
    if (node==null || seen.contains(node)) return; seen.add(node);
    String indent = "  ".repeat(d); Class<?> c = node.getClass();
    String id = tryStr(() -> c.getMethod("getId").invoke(node));
    String text = tryStr(() -> { try { return c.getMethod("getText").invoke(node); } catch(Throwable ignore){ return null; } });
    // Special-case WebView HTML
    if ("javafx.scene.web.WebView".equals(c.getName())) {
      Object eng = c.getMethod("getEngine").invoke(node);
      Object html = eng.getClass().getMethod("executeScript", String.class).invoke(eng, "document.documentElement.outerHTML");
      w.write(indent + "WebView HTML >>>\n" + String.valueOf(html) + "\n" + indent + "<<< END\n");
    }
    w.write(String.format("%s%s id=%s text=%s%n", indent, c.getName(), id, text));
    // Children
    try {
      Class<?> parent = Class.forName("javafx.scene.Parent");
      if (parent.isInstance(node)) {
        java.util.List<?> kids = (java.util.List<?>) c.getMethod("getChildrenUnmodifiable").invoke(node);
        for (Object k : kids) writeFxNodeReflect(w, k, d+1, seen);
      }
    } catch (Throwable ignored) {}
  }
  private static String tryStr(SupplierThrows s){ try{ Object v=s.get(); return v==null? "": v.toString(); }catch(Throwable t){ return ""; } }
  private interface SupplierThrows { Object get() throws Exception; }
}
