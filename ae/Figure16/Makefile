SRC_DIR = src
BIN_DIR = bin

CC = gcc
CFLAGS = -Wall -Wextra -O2
LDFLAGS = -luring -lpthread

BENCH = $(BIN_DIR)/bench

all: $(BENCH)

$(BENCH): $(SRC_DIR)/bench.c
	@mkdir -p $(BIN_DIR)
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

clean:
	rm -rf $(BIN_DIR)/*

.PHONY: all clean
