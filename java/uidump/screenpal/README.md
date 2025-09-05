## VisualVM heapdumps

- Can see images loaded: 
    - `com.screencastomatic.common.bW#6 : 1,600x1,066` => show preview panel
- TODO!! explore a bit more and makes sure you can find meaningful data to use before pursuing same data via jcmd (below) or agent (below)
- FOUND A LABEL! 
    javax.swing.JTextField$AccessibleJTextField#1
        accessibleDescription = java.lang.String#101570 : Search Video Projects


### OQL
DOCS: https://visualvm.github.io/documentation.html
   *** USE THIS FOR QUERY EXAMPLES and DOCS ***
   <!-- select filter(heap.classes(), "/java.net./.test(it.name)") -->
   WORKS: 
     select filter(heap.classes(),  "/com.screencast./.test(it.name)")

   strings with matching contents:

       select {instance: s, content: s.toString()} from java.lang.String s
        where /posbar/.test(s.toString())
             # matches HTML table stuff!

       select {instance: s, content: s.toString()} from java.lang.String s
        where /accessible/.test(s.toString())

       select {instance: s, content: s.toString()} from java.lang.String s
        where /Storyboard/.test(s.toString())

TODO can this work?
    heap.objects("java.lang.String").slice(0, 10).map(s => s.toString())


- Installed plugins:
    GraalJS (i think I need this for the JS type queries)
      required restart
    colorful code one (forgot name)
    synatx completion too

- USEFUL classes in heapdumps:

- seem to be diff syntaxes (USE THE EXAMPLES (JS one) If it won't run some of this)...
    EVERYTHING !!!:
        heap.objects()
        top(heap.objects())
    heap.objects("java.lang.String")

com.screencastomatic.common.CommandServer#1

m_htmlPane = com.screencastomatic.display.EditButton$2#20 : toolbar.edit.footer.help#htmlPane
select x from javax.swing.plaf.ColorUIResource x
select x from com.screencastomatic.display.EditButton x
rootPane = javax.swing.JRootPane#4

loaded classes (in examples):
   select { loader: cl,
             classes: filter(map(cl.classes.elementData, 'it'), 'it != null') }
    from instanceof java.lang.ClassLoader cl

TODO TRY
    com.screencastomatic.editor.body.Edit2Body
    select x from javax.swing.JPanel x

NOT WORKING:
    select x from instanceOf('com.example.*') x
       how to search in pkg namespace?






## jcmd

WHAT all can I find with this command? if it works to get stuff I can run right in hammerspoon lua code!
  classes show up => 
    ./jattach $PID jcmd VM.classes | grep -i editorframe

## jdk troubleshooting

use checkout in: github/openjdk/jdk/src/jdk.attach

## own agent (see java code in this dir)

TODO TEST IT
