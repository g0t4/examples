#include <iostream>
#include <unistd.h>
#include <sys/wait.h>
#include <sched.h>

int main()
{
    printf("\n");

    printf("getpid() = %d\n\n", getpid());

    printf("\n\n");
    return 0;
}
