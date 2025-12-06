/**
 * io_uring Open-Loop Benchmark (Multi-threaded Edition)
 * * 功能:
 * 1. 多线程并发提交 (-j threads)
 * 2. 每个线程独立的 io_uring 实例 (无锁设计)
 * 3. 模拟业务逻辑开销 (-d us)
 * 4. Open-Loop 速率控制 (Total IOPS / Threads)
 * 5. 自动 CPU 绑核 (避免线程挤在一个核上)
 * 6. 优化 io_uring 标志 (SINGLE_ISSUER)
 *
 * 编译: gcc -o io_uring_mt io_uring_mt.c -luring -lpthread
 * 用法: ./io_uring_mt -r 2000000 -d 2 -j 4
 */

 #define _GNU_SOURCE
 #include <stdio.h>
 #include <fcntl.h>
 #include <string.h>
 #include <stdlib.h>
 #include <unistd.h>
 #include <sys/stat.h>
 #include <sys/time.h>
 #include <time.h>
 #include <liburing.h>
 #include <getopt.h>
 #include <errno.h>
 #include <pthread.h>
 #include <sched.h> // for cpu_set_t
 
 // --- 配置 ---
 #define BUFF_SIZE 1             
 #define DEFAULT_FILENAME "/dev/null"
 #define DEFAULT_TARGET_IOPS 100000
//  #define QD 4096 
 #define QD 256 
 
 struct request_data {
     int index;
     unsigned long long issue_ts;
 };
 
 // 线程参数结构体
 struct thread_config {
     int thread_id;
     int num_threads;
     int target_iops_per_thread;
     long max_requests_per_thread;
     int duration_sec;
     int app_delay_us;
     char *filename;
 };
 
 // 线程统计结果
 struct thread_result {
     long submitted;
     long completed;
     long errors;
     long long *latencies; // 动态分配
     long latency_count;
     double elapsed_sec;
 };
 
 // 全局辅助函数
 static inline unsigned long long get_current_ns() {
     struct timespec ts;
     clock_gettime(CLOCK_MONOTONIC, &ts);
     return (unsigned long long)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
 }
 
 static void spin_cpu(unsigned long long us) {
    if (us == 0) return;
    unsigned long long start = get_current_ns();
    unsigned long long target = start + us * 1000ULL;
    while (get_current_ns() < target) {
        __asm__ volatile("" : : : "memory");
    }
 }
 
 int compare_long(const void *a, const void *b) {
     long long la = *(const long long *)a;
     long long lb = *(const long long *)b;
     if (la < lb) return -1;
     if (la > lb) return 1;
     return 0;
 }
 
 // 设置线程亲和性 (绑核)
 void pin_thread_to_core(int thread_id) {
     int num_cores = sysconf(_SC_NPROCESSORS_ONLN);
     if (num_cores <= 0) return;
 
     cpu_set_t cpuset;
     CPU_ZERO(&cpuset);
     // 简单的 Round-Robin 绑核策略
     // 比如 4 个核，线程 0->核0, 线程 1->核1 ...
     int core_id = thread_id % num_cores;
     CPU_SET(core_id, &cpuset);
 
     int s = pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
     if (s != 0) {
         fprintf(stderr, "[Thread %d] Failed to pin to core %d\n", thread_id, core_id);
     } 
     // else {
     //     printf("[Thread %d] Pinned to core %d\n", thread_id, core_id);
     // }
 }
 
 // --- 工作线程逻辑 ---
 void *worker_thread_func(void *arg) {
     struct thread_config *cfg = (struct thread_config *)arg;
     
     // 1. 绑核：这对于高并发测试至关重要
     pin_thread_to_core(cfg->thread_id);
 
     struct thread_result *res = calloc(1, sizeof(struct thread_result));
     struct io_uring ring;
     int fd; 
     
     // 线程内部独立 Open
     fd = open(cfg->filename, O_WRONLY | O_CREAT | O_DIRECT, 0666); 
     if (fd < 0) {
         // Fallback
         fd = open(cfg->filename, O_WRONLY | O_CREAT, 0666);
         if (fd < 0) {
             fprintf(stderr, "[Thread %d] open failed: %s\n", cfg->thread_id, strerror(errno));
             return NULL;
         }
     }
 
     long estimated_samples = (cfg->max_requests_per_thread > 0) ? 
                              cfg->max_requests_per_thread : 
                              (long)cfg->target_iops_per_thread * (cfg->duration_sec + 1);
     
     if (estimated_samples > 50000000) estimated_samples = 50000000;
 
     res->latencies = malloc(sizeof(long long) * estimated_samples);
     struct request_data *reqs = calloc(QD, sizeof(struct request_data));
     char *data_buffer_pool = calloc(QD, BUFF_SIZE);
 
     if (!res->latencies || !reqs || !data_buffer_pool) {
         fprintf(stderr, "[Thread %d] Memory allocation failed\n", cfg->thread_id);
         close(fd);
         return NULL;
     }
 
     struct io_uring_params params;
     memset(&params, 0, sizeof(params));
     
     // [优化] 告诉内核只有一个线程会提交请求，减少内核侧锁开销 (Kernel 6.0+)
 #ifdef IORING_SETUP_SINGLE_ISSUER
     params.flags |= IORING_SETUP_SINGLE_ISSUER;
 #endif 
     // [优化] 允许任务协同运行 (Kernel 5.19+)
 #ifdef IORING_SETUP_COOP_TASKRUN
     params.flags |= IORING_SETUP_COOP_TASKRUN;
 #endif
 
     if (io_uring_queue_init_params(QD, &ring, &params) < 0) {
         // 如果新 flag 不支持导致失败，回退到默认
         memset(&params, 0, sizeof(params));
         if (io_uring_queue_init_params(QD, &ring, &params) < 0) {
             fprintf(stderr, "[Thread %d] io_uring_init failed\n", cfg->thread_id);
             close(fd);
             return NULL;
         }
     }
 
     unsigned long long start_time = get_current_ns();
     unsigned long long end_time = start_time + ((unsigned long long)cfg->duration_sec * 1000000000ULL);
     
     unsigned long long interval_ns = 1000000000ULL / cfg->target_iops_per_thread;
     unsigned long long next_arrival_ns = start_time;
     
     int inflight = 0;
     unsigned long long base_offset = (unsigned long long)cfg->thread_id * 1024ULL * 1024ULL * 1024ULL * 1024ULL;
 
     while (1) {
         unsigned long long now = get_current_ns();
         
         int stop_submitting = 0;
         if (cfg->max_requests_per_thread > 0) {
             if (res->submitted >= cfg->max_requests_per_thread) stop_submitting = 1;
         } else {
             if (now >= end_time) stop_submitting = 1;
         }
 
         if (stop_submitting && inflight == 0) break;
 
         // 提交逻辑
         int added_to_sq = 0;
         while (!stop_submitting && now >= next_arrival_ns && inflight < QD) {
             // [Fix] 记录操作开始的绝对时间（包含 App Delay）
             unsigned long long op_start_ts = now;
 
             if (cfg->app_delay_us > 0) {
                 spin_cpu(cfg->app_delay_us);
                 now = get_current_ns();
             }
 
             struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
             if (!sqe) break; 
 
             int idx = res->submitted % QD;
             struct request_data *req = &reqs[idx];
             req->index = res->submitted;
             // [Fix] 使用 spin 之前的时间戳，这样 Latency = App_Delay + IO_Time
             req->issue_ts = op_start_ts; 
             
             char *buf_ptr = data_buffer_pool + (idx * BUFF_SIZE);
             // *buf_ptr = 'a'; // 去掉赋值操作以极致压测开销
             
             unsigned long long offset = base_offset + (res->submitted * BUFF_SIZE);
 
             io_uring_prep_write(sqe, fd, buf_ptr, BUFF_SIZE, offset);
             io_uring_sqe_set_data(sqe, req);
 
             res->submitted++;
             inflight++;
             next_arrival_ns += interval_ns;
             added_to_sq++;
 
             if (cfg->max_requests_per_thread > 0 && res->submitted >= cfg->max_requests_per_thread) {
                 stop_submitting = 1;
                 break;
             }
         }
 
         // 仅当添加了新请求，或者 SQ 环中有未提交请求时才调用 submit
         if (added_to_sq > 0) {
             io_uring_submit(&ring);
         }
 
         // 收割逻辑
         struct io_uring_cqe *cqe;
         unsigned head;
         int reaped = 0;
 
         io_uring_for_each_cqe(&ring, head, cqe) {
             struct request_data *req = (struct request_data *)io_uring_cqe_get_data(cqe);
             
             if (cqe->res < 0) {
                 res->errors++;
             } else {
                 if (res->latency_count < estimated_samples) {
                     // 仅在未满时采样延迟，减少内存写
                     unsigned long long completion_ts = get_current_ns();
                     res->latencies[res->latency_count++] = (completion_ts - req->issue_ts);
                 }
                 res->completed++; 
             }
             
             reaped++;
             inflight--;
         }
 
         if (reaped > 0) {
             io_uring_cq_advance(&ring, reaped);
         }
     }
 
     res->elapsed_sec = (get_current_ns() - start_time) / 1e9;
     
     io_uring_queue_exit(&ring);
     free(reqs);
     free(data_buffer_pool);
     close(fd);
     
     return res;
 }
 
 int main(int argc, char *argv[]) {
     int opt;
     int total_target_iops = DEFAULT_TARGET_IOPS;
     long total_max_requests = -1; 
     int duration_sec = 5;
     int app_delay_us = 0;
     int num_threads = 1;
     char *filename = DEFAULT_FILENAME;
 
     while ((opt = getopt(argc, argv, "r:n:t:d:j:")) != -1) {
         switch (opt) {
             case 'r': total_target_iops = atoi(optarg); break;
             case 'n': total_max_requests = atol(optarg); break;
             case 't': duration_sec = atoi(optarg); break;
             case 'd': app_delay_us = atoi(optarg); break;
             case 'j': num_threads = atoi(optarg); break;
             default:
                 fprintf(stderr, "Usage: %s -r total_iops -n total_reqs -t sec -d delay_us -j threads\n", argv[0]);
                 return 1;
         }
     }
 
     if (num_threads < 1) num_threads = 1;
     // 如果用户设置的 Total IOPS 太小，保证至少每线程跑 1 IOPS
     if (total_target_iops < num_threads) total_target_iops = num_threads;
 
     printf("Benchmark Config:\n");
     printf("  Threads:    %d (CPU Pinned)\n", num_threads);
     printf("  Target:     %s (bs=%d)\n", filename, BUFF_SIZE);
     printf("  Total IOPS: %d (%d per thread)\n", total_target_iops, total_target_iops / num_threads);
     if (app_delay_us > 0) printf("  App Delay:  %d us\n", app_delay_us);
 
     pthread_t *threads = malloc(sizeof(pthread_t) * num_threads);
     struct thread_config *configs = malloc(sizeof(struct thread_config) * num_threads);
 
     for (int i = 0; i < num_threads; i++) {
         configs[i].thread_id = i;
         configs[i].num_threads = num_threads;
         configs[i].target_iops_per_thread = total_target_iops / num_threads;
         
         if (total_max_requests > 0)
             configs[i].max_requests_per_thread = total_max_requests / num_threads;
         else
             configs[i].max_requests_per_thread = -1;
             
         configs[i].duration_sec = duration_sec;
         configs[i].app_delay_us = app_delay_us;
         configs[i].filename = filename;
 
         if (pthread_create(&threads[i], NULL, worker_thread_func, &configs[i]) != 0) {
             perror("pthread_create");
             exit(1);
         }
     }
 
     long total_submitted = 0;
     long total_completed = 0;
     long total_errors = 0;
     long long *all_latencies = NULL;
     long total_latency_count = 0;
     double max_thread_time = 0;
 
     for (int i = 0; i < num_threads; i++) {
         struct thread_result *res;
         pthread_join(threads[i], (void **)&res);
 
         if (res) {
             total_submitted += res->submitted;
             total_completed += res->completed;
             total_errors += res->errors;
             if (res->elapsed_sec > max_thread_time) max_thread_time = res->elapsed_sec;
 
             if (res->latency_count > 0) {
                 long long *new_ptr = realloc(all_latencies, sizeof(long long) * (total_latency_count + res->latency_count));
                 if (new_ptr) {
                     all_latencies = new_ptr;
                     memcpy(all_latencies + total_latency_count, res->latencies, sizeof(long long) * res->latency_count);
                     total_latency_count += res->latency_count;
                 }
             }
             free(res->latencies); 
             free(res);
         }
     }
 
     printf("\n--- Aggregate Results ---\n");
     printf("Time elapsed:    %.2f s (slowest thread)\n", max_thread_time);
     printf("Reqs submitted:  %ld\n", total_submitted);
     printf("Reqs completed:  %ld\n", total_completed);
     printf("Errors:          %ld\n", total_errors);
     printf("Realized IOPS:   %.2f\n", total_completed / max_thread_time);
     printf("Throughput:      %.2f MiB/s\n", (total_completed * BUFF_SIZE) / (1024.0 * 1024.0) / max_thread_time);
 
     if (total_latency_count > 0) {
         // qsort在大数据量下比较慢，这里仅仅是示例
         printf("Sorting %ld latency samples...\n", total_latency_count);
         qsort(all_latencies, total_latency_count, sizeof(long long), compare_long);
 
         printf("\nLatency (ns):\n");
         printf("  P50:   %lld\n", all_latencies[(long)(total_latency_count * 0.50)]);
         printf("  P90:   %lld\n", all_latencies[(long)(total_latency_count * 0.90)]);
         printf("  P99:   %lld\n", all_latencies[(long)(total_latency_count * 0.99)]);
         printf("  P99.9: %lld\n", all_latencies[(long)(total_latency_count * 0.999)]);
         printf("  Max:   %lld\n", all_latencies[total_latency_count - 1]);
     }
 
     free(all_latencies);
     free(threads);
     free(configs);
 
     return 0;
 }