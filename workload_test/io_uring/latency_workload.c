#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <liburing.h>
#include <time.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>

#define QUEUE_DEPTH 16
#define FILE_TABLE_SIZE 65536
#define BATCH_SUBMIT 8
#define TEST_ITERATIONS 200000
#define LINK_DEPTH 32
#define CQ_ADVANCE_INTERVAL 16
#define IO_SIZE 65536

#define CQ_RING_SIZE 16

int compare_longs(const void *a, const void *b) {
    long la = *(const long *)a;
    long lb = *(const long *)b;
    return (la > lb) - (la < lb);
}

int main() {
    struct io_uring ring;
    int ret, i, j, dev_null_fd;

    long *latencies = malloc(sizeof(long) * TEST_ITERATIONS);
    if (!latencies) {
        perror("Failed to allocate memory for latency results");
        return 1;
    }

    printf("Starting ULTIMATE io_uring latency workload with IO_LINK + ASYNC...\n");
    printf("Using a chain of %d IORING_OP_FILES_UPDATE/fsync ops to maximize pending work.\n", LINK_DEPTH);
    printf("Iterations: %d\n\n", TEST_ITERATIONS);

    dev_null_fd = open("/dev/null", O_RDWR);
    if (dev_null_fd < 0) {
        perror("open /dev/null failed");
        free(latencies);
        return 1;
    }

    int test_fd = open("testfile.tmp", O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (test_fd < 0) {
        perror("open testfile.tmp failed");
        free(latencies);
        return 1;
    }

    char *buf = malloc(IO_SIZE);
    memset(buf, 0xAB, IO_SIZE);

    /*
     * MODIFICATION: Switch to io_uring_queue_init_params to precisely control CQ size.
     * We set cq_entries to our small CQ_RING_SIZE to force overflows, which in turn
     * creates pending local work, thus triggering io_local_work_pending.
     */
    struct io_uring_params params;
    memset(&params, 0, sizeof(params));
    params.cq_entries = CQ_RING_SIZE;
    params.flags = IORING_SETUP_COOP_TASKRUN | IORING_SETUP_SINGLE_ISSUER | IORING_SETUP_DEFER_TASKRUN |
        IORING_SETUP_CQSIZE;

    ret = io_uring_queue_init_params(QUEUE_DEPTH, &ring, &params);
    if (ret < 0) {
        fprintf(stderr, "queue_init_params failed: %s\n", strerror(-ret));
        free(latencies);
        close(dev_null_fd);
        return 1;
    }

    int *fds = malloc(sizeof(int) * FILE_TABLE_SIZE);
    for (i = 0; i < FILE_TABLE_SIZE; i++) fds[i] = dev_null_fd;
    ret = io_uring_register_files(&ring, fds, FILE_TABLE_SIZE);
    if (ret) {
        fprintf(stderr, "io_uring_register_files failed: %s\n", strerror(-ret));
        goto cleanup;
    }

    // This initial flood of submissions will overflow the CQ ring.
    // After this submit call, there will be pending local work,
    // and io_local_work_pending() would return true inside the kernel.
    for (i = 0; i < BATCH_SUBMIT; i++) {
        struct io_uring_sqe *sqe;
        for (j = 0; j < LINK_DEPTH; j++) {
            sqe = io_uring_get_sqe(&ring);
            if (!sqe) {
                goto submit_flood;
            }

            if (j == LINK_DEPTH - 1) {
                io_uring_prep_fsync(sqe, test_fd, 0);
            } else if (j == LINK_DEPTH - 2) {
                io_uring_prep_write(sqe, test_fd, buf, IO_SIZE, 0);
            } else {
                io_uring_prep_read(sqe, test_fd, buf, IO_SIZE, 0);
            }
            sqe->flags |= IOSQE_IO_LINK;
        }
    }
submit_flood:
    io_uring_submit(&ring);

    unsigned long total_latency_ns = 0;
    int actual_iterations = 0;

    struct timespec loop_start_time;
    clock_gettime(CLOCK_MONOTONIC, &loop_start_time);

    for (i = 0; i < TEST_ITERATIONS; i++) {
        for (j = 0; j < LINK_DEPTH; j++) {
            struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
            if (!sqe) {
                io_uring_submit(&ring);
                sqe = io_uring_get_sqe(&ring);
                if (!sqe) {
                    fprintf(stderr, "Failed to get SQE in main loop. Stopping early.\n");
                    goto end_loop;
                }
            }

            if (j == LINK_DEPTH - 1) {
                io_uring_prep_fsync(sqe, test_fd, 0);
            } else if (j == LINK_DEPTH - 2) {
                io_uring_prep_write(sqe, test_fd, buf, IO_SIZE, 0);
            } else {
                io_uring_prep_read(sqe, test_fd, buf, IO_SIZE, 0);
            }
            sqe->flags |= IOSQE_IO_LINK;
        }

        struct timespec start_time;
        clock_gettime(CLOCK_MONOTONIC, &start_time);

        ret = io_uring_submit_and_wait(&ring, 1);
        if (ret < 0) {
            fprintf(stderr, "submit_and_wait failed: %s. Stopping early.\n", strerror(-ret));
            break;
        }

        struct timespec end_time;
        clock_gettime(CLOCK_MONOTONIC, &end_time);

        long latency_ns = (end_time.tv_sec - start_time.tv_sec) * 1e9 +
                          (end_time.tv_nsec - start_time.tv_nsec);

        latencies[i] = latency_ns;
        total_latency_ns += latency_ns;

        actual_iterations++;

        if ((i % CQ_ADVANCE_INTERVAL) == 0) {
            struct io_uring_cqe *cqe;
            unsigned head;
            unsigned count = 0;
            io_uring_for_each_cqe(&ring, head, cqe) {
                count++;
            }
            if (count > 0) {
                io_uring_cq_advance(&ring, count);
            }
        }
    }

end_loop:;
    struct timespec loop_end_time;
    clock_gettime(CLOCK_MONOTONIC, &loop_end_time);

    printf("\nTest finished after %d iterations.\n", actual_iterations);

    if (actual_iterations > 0) {
        qsort(latencies, actual_iterations, sizeof(long), compare_longs);

        long p50_idx = (actual_iterations * 0.50) - 1;
        long p90_idx = (actual_iterations * 0.90) - 1;
        long p99_idx = (actual_iterations * 0.99) - 1;
        long p999_idx = (actual_iterations * 0.999) - 1;
        long p9999_idx = (actual_iterations * 0.9999) - 1;

        p50_idx = p50_idx < 0? 0 : p50_idx;
        p90_idx = p90_idx < 0? 0 : p90_idx;
        p99_idx = p99_idx < 0? 0 : p99_idx;
        p999_idx = p999_idx < 0? 0 : p999_idx;
        p9999_idx = p9999_idx < 0? 0 : p9999_idx;

        double avg_latency_us = (double)total_latency_ns / actual_iterations / 1000.0;
        double p50_us = (double)latencies[p50_idx] / 1000.0;
        double p90_us = (double)latencies[p90_idx] / 1000.0;
        double p99_us = (double)latencies[p99_idx] / 1000.0;
        double p999_us = (double)latencies[p999_idx] / 1000.0;
        double p9999_us = (double)latencies[p9999_idx] / 1000.0;

        printf("\n--- Latency Statistics ---\n");
        printf("p50:\t\t%.2f us\n", p50_us);
        printf("Average:\t%.2f us\n", avg_latency_us);
        printf("p90:\t\t%.2f us\n", p90_us);
        printf("p99:\t\t%.2f us\n", p99_us);
        printf("p99.9:\t\t%.2f us\n", p999_us);
        printf("p99.99:\t\t%.2f us\n", p9999_us);

        double total_duration_s = (loop_end_time.tv_sec - loop_start_time.tv_sec) +
                                  (loop_end_time.tv_nsec - loop_start_time.tv_nsec) / 1e9;
        double throughput_ops_per_sec = actual_iterations / total_duration_s;

        printf("\n--- Throughput Statistics ---\n");
        printf("Ops/sec:\t%.2f\n", throughput_ops_per_sec);
    }

cleanup:
    io_uring_queue_exit(&ring);
    close(dev_null_fd);
    close(test_fd);
    unlink("testfile.tmp");
    free(fds);
    free(latencies);
    free(buf);

    return 0;
}