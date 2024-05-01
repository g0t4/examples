CC=g++
CFLAGS=-Wall -g

# default
all: fork.out final.out

final.out: final.cpp
	$(CC) $(CFLAGS) -o final.out final.cpp

fork.out: fork.cpp
	$(CC) $(CFLAGS) -o fork.out fork.cpp

clean:
	rm -f *.out
