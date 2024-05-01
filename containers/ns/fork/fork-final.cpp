#include <iostream>
#include <unistd.h>   // for fork()
#include <sys/wait.h> // for wait()
#include <sched.h>    // for unshare()

int main()
{
    printf("\n");

    printf("getpid(): %d\n", getpid());

    //unshare(CLONE_NEWPID); // ignore failures to keep code readabl-er
    pid_t fork_pid = fork();
    // move unshare here (after fork) to show difference in PIDs for child

    if (fork_pid > 0)
    {

        wait(NULL);
        printf("... wait finished\n\n");

        printf("[PARENT] fork_pid: %d, getpid(): %d\n", fork_pid, getpid());
        system("ps faux");
    }
    else if (fork_pid == 0)
    {
        printf("[CHILD] fork_pid: %d, getpid(): %d\n", fork_pid, getpid());
        system("ps faux");
        exit(0);
    }

    printf("\n\n");
    return 0;
}
