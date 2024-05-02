#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <unistd.h>
#include <sys/wait.h>
#include <sched.h>

using namespace std;

int main()
{
    printf("\n");

    cout << "getpid() = " << getpid() << endl;
    unshare(CLONE_NEWPID);
    cout << "getpid() = " << getpid() << endl;

    cout << "before fork\n";
    int fork_pid = fork();
    cout << "after fork\n";
    if (fork_pid == 0)
    {
        // child
        cout << "[Child] " << getpid() << ", fork_pid=" << fork_pid << endl;
    }
    else if (fork_pid > 0)
    {
        // parent
        cout << "[Parent] " << getpid() << ", fork_pid=" << fork_pid << endl;
    }

    printf("\n\n");
    return 0;
}
