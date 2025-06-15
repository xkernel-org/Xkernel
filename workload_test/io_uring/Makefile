CC=gcc
CFLAGS=-g -O2 -Wall -I/usr/include/liburing
LDFLAGS=-luring

all: latency_workload

latency_workload: latency_workload.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f latency_workload