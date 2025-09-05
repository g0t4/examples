

working:
```sh
java SleepMain # run separate tab
jps -l # get PID
./jattach 82088 load instrument false hello-agent.jar
# works!


# list cmds
./jattach 18560 jcmd help -all


# useful to see what this app uses (instead of just digging on disk in files)
./jattach 18560 jcmd VM.classes
```
