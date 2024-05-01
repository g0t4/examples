#include <iostream>
#include <unistd.h>   // for fork()
#include <sys/wait.h> // for wait()

int main()
{
    printf("\n");

    printf("PID: %d\n", getpid());

    pid_t fork_pid = fork();

    if (fork_pid > 0)
    {
        printf("fork_pid: %d, getpid(): %d\n", fork_pid, getpid());

        wait(NULL);
        printf("... wait finished");
    }
    else if (fork_pid == 0)
    {
        printf("fork_pid: %d, getpid(): %d\n", fork_pid, getpid());
        exit(0);
    }

    printf("\n\n");
    return 0;
}
