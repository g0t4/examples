package com.repl;

import java.awt.*;
import java.awt.event.*;
import java.beans.*;
import java.lang.reflect.*;
import java.util.*;

import javax.accessibility.Accessible;
import javax.accessibility.AccessibleContext;

// TODO HAVE NOT YET TRIED THIS, chatgpt made this one
//  this looks way more promising vs what Claude came up with 
// *** NOTABLY looking at Accessibility info on controls might be useful

public final class ComponentInspector {

    public static void inspect(Component component) {
        System.out.println("=== Component Inspector ===");
        printClassHierarchy(component);
        printInterfaces(component);
        printBeanProperties(component);
        printPublicMethods(component);
        printDeclaredFields(component);
        printListeners(component);
        printChildren(component);
    }

    public static void printClassHierarchy(Component component) {
        System.out.println("\n-- Class Hierarchy --");
        Class<?> type = component.getClass();
        while (type != null) {
            System.out.println(type.getName());
            type = type.getSuperclass();
        }
    }

    public static void printInterfaces(Component component) {
        System.out.println("\n-- Implemented Interfaces --");
        for (Class<?> iface : component.getClass().getInterfaces()) {
            System.out.println(iface.getName());
        }
    }

    public static void printBeanProperties(Component component) {
        System.out.println("\n-- JavaBeans Properties (via Introspector) --");
        try {
            BeanInfo beanInfo = Introspector.getBeanInfo(component.getClass(), Object.class);
            for (PropertyDescriptor pd : beanInfo.getPropertyDescriptors()) {
                Method getter = pd.getReadMethod();
                if (getter != null) {
                    try {
                        Object value = getter.invoke(component);
                        System.out.printf("%s (%s) = %s%n",
                                pd.getName(),
                                pd.getPropertyType() != null ? pd.getPropertyType().getSimpleName() : "unknown",
                                safeToString(value));
                    } catch (Throwable ignored) {
                        System.out.printf("%s = <inaccessible or threw>%n", pd.getName());
                    }
                }
            }
            System.out.println("\n-- JavaBeans Methods --");
            for (MethodDescriptor md : beanInfo.getMethodDescriptors()) {
                System.out.println(signature(md.getMethod()));
            }
        } catch (IntrospectionException e) {
            System.out.println("Introspection failed: " + e);
        }
    }

    public static void printPublicMethods(Component component) {
        System.out.println("\n-- Public Methods (Class.getMethods) --");
        for (Method m : component.getClass().getMethods()) {
            System.out.println(signature(m));
        }
    }

    public static void printDeclaredFields(Object component) {
        System.out.println("\n-- Declared Fields (including private) --");
        Class<?> type = component.getClass();
        Set<String> seen = new LinkedHashSet<>();
        while (type != null) {
            for (Field f : type.getDeclaredFields()) {
                if (seen.add(type.getName() + "#" + f.getName())) {
                    try {
                        f.setAccessible(true); // requires --add-opens in JPMS world
                        Object value = f.get(component);
                        // careful how you modify the following, if you use "".formatted you lose value display?!
                        // but it did fix the new line everywhere nonsense...
                        // anyways, this is how I found tempRectangles
                        System.out.printf("%s %s.%s = %s%n",
                                Modifier.toString(f.getModifiers()),
                                type.getName(),
                                // field name:
                                f.getName(),
                                safeToString(value));
                    } catch (Throwable t) {
                        System.out.printf("%s %s.%s = <inaccessible or threw>%n",
                                Modifier.toString(f.getModifiers()), type.getName(), f.getName());
                    }
                }
            }
            type = type.getSuperclass();
        }
    }

    private static void printListeners(Component component) {
        System.out.println("\n-- Attached Listeners (common AWT types) --");
        Map<String, Object[]> listeners = new LinkedHashMap<>();
        listeners.put("ComponentListener", component.getComponentListeners());
        listeners.put("ContainerListener", component instanceof Container
                ? ((Container) component).getContainerListeners()
                : new ContainerListener[0]);
        listeners.put("FocusListener", component.getFocusListeners());
        listeners.put("HierarchyListener", component.getHierarchyListeners());
        listeners.put("HierarchyBoundsListener", component.getHierarchyBoundsListeners());
        listeners.put("InputMethodListener", component.getInputMethodListeners());
        listeners.put("KeyListener", component.getKeyListeners());
        listeners.put("MouseListener", component.getMouseListeners());
        listeners.put("MouseMotionListener", component.getMouseMotionListeners());
        listeners.put("MouseWheelListener", component.getMouseWheelListeners());

        for (Map.Entry<String, Object[]> e : listeners.entrySet()) {
            System.out.println(e.getKey() + ":");
            for (Object l : e.getValue())
                System.out.println("  " + l);
        }

        // Try generic getListeners(Class) via reflection to discover custom listener types
        System.out.println("\n-- getListeners(Class) scan --");
        try {
            Method getListeners = Component.class.getMethod("getListeners", Class.class);
            for (Class<?> i : component.getClass().getInterfaces()) {
                if (i.getName().endsWith("Listener")) {
                    Object[] arr = (Object[]) getListeners.invoke(component, i);
                    if (arr.length > 0) {
                        System.out.println(i.getName() + ":");
                        for (Object o : arr)
                            System.out.println("  " + o);
                    }
                }
            }
        } catch (Throwable ignored) {
        }
    }

    private static void printChildren(Component component) {
        if (component instanceof Container) {
            System.out.println("\n-- Children (Container.getComponents) --");
            for (Component child : ((Container) component).getComponents()) {
                System.out.println(child.getClass().getName() + "  bounds=" + child.getBounds());
            }
        } else {
            System.out.println("\n-- Children --\n(not a Container)");
        }

        // Accessibility can expose virtual/hidden structure:
        try {
            AccessibleContext ac = component.getAccessibleContext();
            if (ac != null) {
                System.out.println("\n-- Accessibility Tree (may reveal virtual children) --");
                int count = ac.getAccessibleChildrenCount();
                for (int i = 0; i < count; i++) {
                    Accessible child = ac.getAccessibleChild(i);
                    AccessibleContext cc = child != null ? child.getAccessibleContext() : null;
                    System.out.println((cc != null ? cc.getClass().getName() : "<unknown>")
                            + " role=" + (cc != null ? cc.getAccessibleRole() : "<unknown>")
                            + " name=" + (cc != null ? cc.getAccessibleName() : "<null>"));
                }
            }
        } catch (Throwable t) {
            System.out.println("Accessibility scan failed: " + t.getMessage());
        }
    }

    public static String signature(Method m) {
        StringBuilder b = new StringBuilder();
        b.append(Modifier.toString(m.getModifiers())).append(" ")
                .append(m.getReturnType().getTypeName()).append(" ")
                .append(m.getDeclaringClass().getName()).append(".")
                .append(m.getName()).append("(");
        Class<?>[] params = m.getParameterTypes();
        for (int i = 0; i < params.length; i++) {
            if (i > 0)
                b.append(", ");
            b.append(params[i].getTypeName());
        }
        b.append(")");
        return b.toString();
    }

    public static String safeToString(Object value) {
        if (value == null)
            return "null";
        try {
            return String.valueOf(value);
        } catch (Throwable t) {
            return "<toString threw " + t.getClass().getSimpleName() + ">";
        }
    }
}
