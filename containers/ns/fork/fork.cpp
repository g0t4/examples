#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <unistd.h>
#include <sys/wait.h>
#include <sched.h>

int main()
{
    printf("\n");

    cout << "getpid() = " << getpid() << endl;

    printf("\n\n");
    return 0;
}
