package com.repl;

import java.lang.reflect.*;
import java.util.*;

public final class ObjectInspector {

    public static void printDeclaredFields(Object object) {
        System.out.println("\n-- Declared Fields (including private) --");
        Class<?> type = object.getClass();
        Set<String> seen = new LinkedHashSet<>();
        while (type != null) {
            for (Field f : type.getDeclaredFields()) {
                if (seen.add(type.getName() + "#" + f.getName())) {
                    try {
                        f.setAccessible(true); // requires --add-opens in JPMS world
                        Object value = f.get(object);
                        // careful how you modify the following, if you use "".formatted you lose value display?!
                        // but it did fix the new line everywhere nonsense...
                        // anyways, this is how I found tempRectangles
                        System.out.printf("%s %s.%s = %s%n",
                                Modifier.toString(f.getModifiers()),
                                type.getName(),
                                // field name:
                                f.getName(),
                                ComponentInspector.safeToString(value));
                    } catch (Throwable t) {
                        System.out.printf("%s %s.%s = <inaccessible or threw>%n",
                                Modifier.toString(f.getModifiers()), type.getName(), f.getName());
                    }
                }
            }
            type = type.getSuperclass();
        }
    }

}
