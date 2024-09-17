
.PHONY: all clean

all: ds18b20.c
	gcc -o ds18b20.out ds18b20.c -lgpiod

# -lwiringPi # PRN try this lib?

clean:
	rm -f *.out
