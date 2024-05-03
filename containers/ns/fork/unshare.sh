

# *** unshare command reference:

# unshare(CLONE_NEWPID) equivalent to:
unshare --pid/-p
#    parsed: https://github.com/util-linux/util-linux/blob/e3192bfd1dd129c70f5416e1464135d8cd22c956/sys-utils/unshare.c#L892-L896
#    unshare called: https://github.com/util-linux/util-linux/blob/e3192bfd1dd129c70f5416e1464135d8cd22c956/sys-utils/unshare.c#L1025-L1026

# fork() equivalent to:
unshare --fork/-f
#    parsed: https://github.com/util-linux/util-linux/blob/e3192bfd1dd129c70f5416e1464135d8cd22c956/sys-utils/unshare.c#L869-L871
#    fork called: https://github.com/util-linux/util-linux/blob/e3192bfd1dd129c70f5416e1464135d8cd22c956/sys-utils/unshare.c#L1054-L1069

# combined:
unshare --fork --pid
unshare -f -p


unshare --mount-proc
#   mount -t proc proc /proc
#   https://github.com/util-linux/util-linux/blob/e3192bfd1dd129c70f5416e1464135d8cd22c956/sys-utils/unshare.c#L1164-L1180

# PID+mount ns + remount /proc:
unshare --fork -pm --mount-proc bash



# FYI kernel syscalls:
#
#   unshare()
#     ag -i "syscall_define.*unshare" torvalds/linux
#     https://github.com/torvalds/linux/blob/18daea77cca626f590fb140fc11e3a43c5d41354/kernel/fork.c#L3392-L3395
#     => ksys_unshare: https://github.com/torvalds/linux/blob/18daea77cca626f590fb140fc11e3a43c5d41354/kernel/fork.c#L3273-L3274
#
#   fork()
#      ag -i "syscall_define.*fork" torvalds/linux
#      https://github.com/torvalds/linux/blob/18daea77cca626f590fb140fc11e3a43c5d41354/kernel/fork.c#L2879-L2880
