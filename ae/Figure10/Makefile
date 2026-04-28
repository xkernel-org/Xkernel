SRC_DIR = src
BIN_DIR = bin
RES_DIR = results

SRCS := $(wildcard $(SRC_DIR)/*.c)
TARGETS := $(SRCS:$(SRC_DIR)/%.c=$(BIN_DIR)/%)

CC = gcc
CFLAGS = -Wall -Wextra -O2

all: $(TARGETS)

$(BIN_DIR)/%: $(SRC_DIR)/%.c
	@mkdir -p $(BIN_DIR)
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -rf $(BIN_DIR)/* $(RES_DIR)

.PHONY: all clean
