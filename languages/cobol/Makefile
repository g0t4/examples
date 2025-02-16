# Compiler
COBOL = cobc
CFLAGS = -x  # -x flag creates an executable

# Directories
BIN = bin

# Files
SOURCES = $(wildcard *.cob)
EXECUTABLES = $(patsubst %.cob, $(BIN)/%, $(SOURCES))

# Default target
all: $(EXECUTABLES)

# Compile COBOL files
$(BIN)/%: %.cob | $(BIN)
	$(COBOL) $(CFLAGS) -o $@ $<

# Create bin directory if it doesn't exist
$(BIN):
	mkdir -p $(BIN)

# Clean build artifacts
clean:
	rm -rf $(BIN)/*

.PHONY: all clean

