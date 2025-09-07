## UI observations controls for editor

timeline seems to be a painted control, that ItemService drives
// _ KEY timeline findings:
// Driver: ItemService manages timeline data and state
// Canvas: ItemComponent renders the timeline visually
// Layout: Custom layout manager `fU` positions components
//
// Mouse events → `fT` class (likely ItemService event handler)
// → Updates timeline state → Triggers repaint of ItemComponent
//
// _ other observations:
// JTextPane components hold css style in html, many have empty body
// Saved date/time control (left of undo) has content
//
// Class: com.screencastomatic.common.html.SomHTMLEditorKit
// Extends: javax.swing.text.html.HTMLEditorKit
// Purpose: Custom HTML rendering engine for ScreenPal UI components

## compile examples sent over socket:

# ## no JDK compiler it seems (hence need for Janino)

screenpal clearly won't have the JDK compiler available as it cannot find javax:

```java
javax.tools.JavaCompiler compiler = javax.tools.ToolProvider.getSystemJavaCompiler();
ctx.log("compiler: " + compiler);
```

this results in :

ERR org.codehaus.commons.compiler.CompileException: Line 5, Column 27: Line 5, Column 27: Cannot determine simple type name "javax
