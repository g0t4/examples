

# unshare(CLONE_NEWPID) equivalent to:
unshare --pid/-p
# fork() equivalent to:
unshare --fork/-f
# combined:
unshare --fork --pid
unshare -f -p


