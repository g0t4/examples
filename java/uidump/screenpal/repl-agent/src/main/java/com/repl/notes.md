## ChatGPT's AccessibilityInspector

TIMELINE has this and it looks interesting (on a __field  called tempRectangles__)... not sure if it matters but it was box like!
09/07/25 02:56:22 INFO T0026: tempRectangles
09/07/25 02:56:22 INFO T0026: =
09/07/25 02:56:22 INFO T0026: [java.awt.Rectangle[x=0,y=0,width=0,height=0], java.awt.Rectangle[x=0,y=0,width=16,height=16], java.awt.Rectangle[x=20,y=0,width=16,height=16], java.awt.Rectangle[x=0,y=0,width=89,height=20], java.awt.Rectangle[x=0,y=0,width=89,height=20], java.awt.Rectangle[x=0,y=0,width=246,height=24], java.awt.Rectangle[x=0,y=0,width=246,height=30], java.awt.Rectangle[x=0,y=0,width=34,height=37], java.awt.Rectangle[x=5,y=0,width=38,height=39], java.awt.Rectangle[x=0,y=0,width=32,height=32], java.awt.Rectangle[x=0,y=0,width=77,height=35], java.awt.Rectangle[x=0,y=0,width=77,height=35], java.awt.Rectangle[x=0,y=0,width=87,height=35], java.awt.Rectangle[x=133,y=0,width=129,height=39], java.awt.Rectangle[x=930,y=43,width=0,height=0], java.awt.Rectangle[x=30,y=15,width=1860,height=43], java.awt.Rectangle[x=0,y=0,width=1920,height=73], java.awt.Rectangle[x=0,y=0,width=1920,height=73], java.awt.Rectangle[x=0,y=0,width=1920,height=784], java.awt.Rectangle[x=1576,y=36,width=5,height=15]]

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
