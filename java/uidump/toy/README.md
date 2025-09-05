

working:
```sh
java SleepMain # run separate tab
jps -l # get PID
./jattach 82088 load instrument false hello-agent.jar
# works!
```
