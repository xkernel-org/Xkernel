#include <iostream>
#include <vector>
#include <thread>
#include <chrono>
#include <random>
#include <numeric>
#include <algorithm>

bool early_stop = false;

// Each thread will allocate its own private memory region.
// This function simulates a memory-intensive workload by continuously
// accessing and modifying a large block of memory for a fixed number of rounds.
void memory_intensive_task(int thread_id, size_t memory_size_mb, int rounds) {
    size_t memory_size_bytes = memory_size_mb * 1024 * 1024;
    size_t num_elements = memory_size_bytes / sizeof(long);

    // Allocate a large vector and fill it with data to ensure
    // the memory pages are actually allocated by the OS.

    // Compare with sysbench
    // Here - one computation each memcpy (long)
    // sysbench - one computation each 1kB
    std::vector<long> memory_block(num_elements);
    std::iota(memory_block.begin(), memory_block.end(), 0);

    if (early_stop) {
        return;
    }

    std::cout << "Thread " << thread_id << " allocated " << memory_size_mb << " MB of memory." << std::endl;

    // Access memory for a specified number of rounds.
    volatile long sum = 0; // Use volatile to prevent compiler optimizations
    for (int i = 0; i < rounds; ++i) {
        for (size_t j = 0; j < num_elements; ++j) {
            sum += memory_block[j];
        }
    }
    std::cout << "Thread " << thread_id << " finished." << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cerr << "Usage: " << argv[0] << " <num_threads> <memory_mb_per_thread> <rounds> <early_stop>" << std::endl;
        return 1;
    }

    int num_threads = std::stoi(argv[1]);
    size_t memory_mb_per_thread = std::stoull(argv[2]);
    int rounds = std::stoi(argv[3]);
    early_stop = std::stoi(argv[4]);

    std::cout << "Starting benchmark with " << num_threads << " threads." << std::endl;
    std::cout << "Each thread will allocate " << memory_mb_per_thread << " MB of memory." << std::endl;
    std::cout << "Each thread will perform " << rounds << " rounds of memory access." << std::endl;

    auto start_time = std::chrono::high_resolution_clock::now();

    std::vector<std::thread> threads;
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back(memory_intensive_task, i, memory_mb_per_thread, rounds);
    }

    for (auto& t : threads) {
        t.join();
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end_time - start_time;
    std::cout << "Benchmark finished in " << elapsed.count() << " seconds." << std::endl;

    return 0;
}
