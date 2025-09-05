#!/usr/bin/env fish

jps -lv # find process ID 
set PID 18560

jcmd $PID VM.command_line
jcmd $PID VM.flags
jcmd $PID VM.system_properties

