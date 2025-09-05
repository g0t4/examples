package com.agenty;

import java.io.PrintStream;
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;
import java.security.ProtectionDomain;

public final class Agenty {
    private static volatile ClassFileTransformer transformer;

    public static Object start(Instrumentation inst, String opts) throws Exception {
        PrintStream out = System.out; // goes wherever the app wired it
        out.println("[agenty] start-03; opts=" + opts);

        transformer = new ClassFileTransformer() {
            @Override
            public byte[] transform(Module m, ClassLoader l, String name,
                    Class<?> c, ProtectionDomain d, byte[] b) {
                // modify or observe classes here (or no-op)
                return null;
            }
        };
        inst.addTransformer(transformer, true);

        // Return an AutoCloseable so bootstrap can call close() on unload.
        return (AutoCloseable) () -> {
            out.println("[agenty] stop");
            if (transformer != null) {
                inst.removeTransformer(transformer);
                transformer = null;
            }
        };
    }
}
