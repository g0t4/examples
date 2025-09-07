package com.repl;

import java.lang.reflect.Field;

public class ReflectDemo {
    public static Object getPrivateField(Object target, String fieldName) throws Exception {
        Class<?> clazz = target.getClass();
        Field field = clazz.getDeclaredField(fieldName);
        field.setAccessible(true); // bypass private/protected
        return field.get(target);
    }

    public static void setPrivateField(Object target, String fieldName, Object value) throws Exception {
        Class<?> clazz = target.getClass();
        Field field = clazz.getDeclaredField(fieldName);
        field.setAccessible(true);
        field.set(target, value);
    }
}
