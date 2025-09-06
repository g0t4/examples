# compile examples sent over socket:

## no JDK compiler it seems (hence need for Janino)

screenpal clearly won't have the JDK compiler available as it cannot find javax:
```java
javax.tools.JavaCompiler compiler = javax.tools.ToolProvider.getSystemJavaCompiler();
ctx.log("compiler: " + compiler);
```
this results in :

ERR org.codehaus.commons.compiler.CompileException: Line 5, Column 27: Line 5, Column 27: Cannot determine simple type name "javax

