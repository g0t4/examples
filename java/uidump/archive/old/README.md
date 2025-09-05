## left off notes

I was using chatgpt to see how it would do with guiding me through attaching and (maybe) dumping controls in a java app (screenpal)
- it helped me get a dummy sleep app working, attached to
- but not screenpal... I suspect smth with how its a native app might be an issue
- dumping info about the VM for screenpal made it look promising but never worked
- in the future, if I want to use this... I should dive a bit more into how attach works (and doesn't) and see what might be an issue myself instead of chatgpt debugging in circles
- ACTUALLY give it codex access!

- BTW I downloaded jattach (to avoid issues with my own AttachAndLoad.java (albiet mine worked fine with the sleep dummy app)
    https://github.com/jattach/jattach/releases
    jattach

TODO explore jattach more myself:
```sh
jps -l  # find PIDs of java VMs
jattach <pid> jcmd help -all

```
