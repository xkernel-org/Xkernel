#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <liburing.h>
#include <time.h>

#define QUEUE_DEPTH 256
#define BATCH_SUBMIT 128 // Number of NOPs to submit initially to flood the queue
#define TEST_ITERATIONS 100000 // Number of latency measurements to take

// A simple structure to hold timing information
struct request {
    struct timespec start_time;
};

int main() {
    struct io_uring ring;
    struct io_uring_sqe *sqe;
    struct io_uring_cqe *cqe;
    int ret, i;
    unsigned long total_latency_ns = 0;

    // IMPORTANT: This workload is designed to show a performance difference
    // if you could change the kernel constant IO_LOCAL_TW_DEFAULT_MAX.
    // A value of 8 would perform better here than the default of 20 because
    // this test is sensitive to single-operation latency, not overall throughput.
    printf("Starting io_uring latency workload...\n");
    printf("This test measures the latency of single submit/reap cycles under a heavy completion load.\n");
    printf("A smaller IO_LOCAL_TW_DEFAULT_MAX would reduce the time the kernel spends\n");
    printf("processing completions in the application's context, lowering the measured latency.\n\n");


    // 1. Initialize io_uring
    ret = io_uring_queue_init(QUEUE_DEPTH, &ring, 0);
    if (ret < 0) {
        fprintf(stderr, "queue_init failed: %s\n", strerror(-ret));
        return 1;
    }

    // 2. Flood the submission queue with NOP operations to create a backlog
    // of completions. This ensures the kernel always has work to do.
    for (i = 0; i < BATCH_SUBMIT; i++) {
        sqe = io_uring_get_sqe(&ring);
        if (!sqe) {
            fprintf(stderr, "Could not get SQE.\n");
            break;
        }
        io_uring_prep_nop(sqe);
    }
    io_uring_submit(&ring);

    // 3. Main measurement loop
    for (i = 0; i < TEST_ITERATIONS; i++) {
        // Get a submission entry
        sqe = io_uring_get_sqe(&ring);
        if (!sqe) {
            // Wait for space in the submission queue if it's full
            io_uring_submit(&ring);
            sqe = io_uring_get_sqe(&ring);
            if (!sqe) {
                 fprintf(stderr, "Failed to get SQE even after submit.\n");
                 break;
            }
        }
        
        // Prepare a new NOP request
        io_uring_prep_nop(sqe);
        
        // Record the start time right before submitting
        struct timespec start_time;
        clock_gettime(CLOCK_MONOTONIC, &start_time);

        // Submit the request and wait for exactly one completion.
        // The time spent inside `io_uring_submit_and_wait` is our measurement.
        // The kernel's task_work will run during this call, processing
        // a batch of completions and delaying the return.
        ret = io_uring_submit_and_wait(&ring, 1);
        if (ret < 0) {
            fprintf(stderr, "submit_and_wait failed: %s\n", strerror(-ret));
            break;
        }

        // Record the end time
        struct timespec end_time;
        clock_gettime(CLOCK_MONOTONIC, &end_time);

        // Calculate the latency in nanoseconds for this single operation
        long latency_ns = (end_time.tv_sec - start_time.tv_sec) * 1000000000L;
        latency_ns += (end_time.tv_nsec - start_time.tv_nsec);
        total_latency_ns += latency_ns;

        // Reap the completion(s) to clear the completion queue.
        // We peek because submit_and_wait already told us there's at least one.
        unsigned head;
        unsigned count = 0;
        io_uring_for_each_cqe(&ring, head, cqe) {
            count++;
        }
        io_uring_cq_advance(&ring, count);
    }

    // 4. Clean up and print results
    io_uring_queue_exit(&ring);

    if (i > 0) {
      double avg_latency = (double)total_latency_ns / i;
      printf("Test finished.\n");
      printf("Average latency per operation: %.2f nanoseconds.\n", avg_latency);
    }

    return 0;
}