# Makefile

SRC_DIR = src
BIN_DIR = bin

SRCS := $(wildcard $(SRC_DIR)/*.c)

TARGETS := $(SRCS:$(SRC_DIR)/%.c=$(BIN_DIR)/%)

CC = gcc
CFLAGS = -Wall -Wextra -O2

all: $(TARGETS)

$(BIN_DIR)/%: $(SRC_DIR)/%.c
	@mkdir -p $(BIN_DIR)
	$(CC) $(CFLAGS) $< -o $@

run: $(TARGETS)
	@echo "Running $(BIN_DIR)/$(notdir $(TARGETS))..."
	./$(BIN_DIR)/$(notdir $(TARGETS))

clean:
	rm -rf $(BIN_DIR)/*

.PHONY: all clean run
