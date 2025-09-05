package com.reloader;

import java.io.Closeable;
import java.lang.instrument.Instrumentation;
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.Objects;

public final class ReloaderAgent {
  private static volatile LoaderHandle current;

  public static void premain(String args, Instrumentation inst) throws Exception {
    agentmain(args, inst);
  }

  public static void agentmain(String args, Instrumentation inst) throws Exception {
    AgentArgs a = AgentArgs.parse(args); // impl=/path/to/impl.jar,class=com.acme.AgentEntry,action=load|reload|unload,opts=...
    String action = a.action == null ? "reload" : a.action;

    switch (action) {
      case "unload" -> unload();
      case "load" -> load(a, inst);
      case "reload" -> { unload(); load(a, inst); }
      default -> throw new IllegalArgumentException("Unknown action: " + action);
    }
  }

  private static synchronized void load(AgentArgs a, Instrumentation inst) throws Exception {
    Objects.requireNonNull(a.impl, "impl (path to impl jar) is required");
    Objects.requireNonNull(a.className, "class (entrypoint FQCN) is required");

    URLClassLoader loader = new URLClassLoader(new URL[]{new URL("file:" + a.impl)},
        ReloaderAgent.class.getClassLoader()); // parent can be null if you want full isolation

    Class<?> entry = Class.forName(a.className, true, loader);
    // Convention: static Object start(Instrumentation, String opts) returning Closeable/AutoCloseable or null
    Method start = entry.getDeclaredMethod("start", Instrumentation.class, String.class);
    Object closable = start.invoke(null, inst, a.opts == null ? "" : a.opts);

    current = new LoaderHandle(loader, (closable instanceof AutoCloseable ac) ? ac : null);
  }

  private static synchronized void unload() {
    LoaderHandle h = current;
    current = null;
    if (h == null) return;
    try { if (h.stopper != null) h.stopper.close(); } catch (Throwable ignored) {}
    try { h.loader.close(); } catch (Throwable ignored) {}
    // After this, with no strong refs, the impl classes and loader are GC-eligible.
  }

  // --- helpers ---
  private record LoaderHandle(URLClassLoader loader, AutoCloseable stopper) {}
  private static final class AgentArgs {
    final String impl, className, action, opts;
    private AgentArgs(String impl, String className, String action, String opts) {
      this.impl = impl; this.className = className; this.action = action; this.opts = opts;
    }
    static AgentArgs parse(String s) {
      String impl=null, cls=null, act=null, opts=null;
      if (s != null && !s.isEmpty()) {
        for (String kv : s.split(",")) {
          String[] p = kv.split("=", 2);
          if (p.length != 2) continue;
          switch (p[0]) {
            case "impl" -> impl = p[1];
            case "class" -> cls = p[1];
            case "action" -> act = p[1];
            case "opts" -> opts = p[1];
          }
        }
      }
      return new AgentArgs(impl, cls, act, opts);
    }
  }
}
