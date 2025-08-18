#include <iostream>
#include <vector>
#include <thread>
#include <chrono>
#include <numeric>
#include <pthread.h>

std::vector<long>* memory_block = nullptr;

bool early_stop = false;
bool intentional_remote = false;
bool pin_cpu = true;

void init_memory(size_t memory_size_mb) {
    size_t memory_size_bytes = memory_size_mb * 1024 * 1024;
    size_t num_elements = memory_size_bytes / sizeof(long);

    // Allocate a large vector and fill it with data to ensure
    // the memory pages are actually allocated by the OS.
    memory_block = new std::vector<long>(num_elements);
    // TODO impacts of iota
    std::iota(memory_block->begin(), memory_block->end(), 0);
}

// This function simulates a memory-intensive workload by continuously
// accessing and modifying a large block of memory for a fixed number of rounds.
void memory_intensive_task(int thread_id, size_t memory_size_mb, int rounds) {
    size_t memory_size_bytes = memory_size_mb * 1024 * 1024;
    size_t num_elements = memory_size_bytes / sizeof(long);

    // Access memory for a specified number of rounds.
    volatile long sum = 0; // Use volatile to prevent compiler optimizations
    for (int i = 0; i < rounds; ++i) {
        for (size_t j = 0; j < num_elements; ++j) {
            sum += (*memory_block)[j];
        }
    }
    std::cout << "Thread " << thread_id << " finished." << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc != 6) {
        std::cerr << "Usage: " << argv[0] << " <num_threads> <total_mb> <rounds> <early_stop> <intentional_remote> <pin_cpu>" << std::endl;
        return 1;
    }

    int num_threads = std::stoi(argv[1]);
    size_t total_mb = std::stoull(argv[2]);
    int rounds = std::stoi(argv[3]);
    early_stop = std::stoi(argv[4]);
    intentional_remote = std::stoi(argv[5]);
    pin_cpu = std::stoi(argv[6]);

    if (pin_cpu) {
        // Pin the main thread to CPU 0
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        CPU_SET(0, &cpuset);
        int rc = pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
        if (rc != 0) {
            std::cerr << "Error calling pthread_setaffinity_np: " << rc << "\n";
        }
    }

    std::cout << "Starting benchmark with " << num_threads << " threads." << std::endl;
    std::cout << "The program will in total allocate " << total_mb << " MB of memory." << std::endl;
    std::cout << "Each thread will perform " << rounds << " rounds of memory access." << std::endl;

    auto start_time = std::chrono::high_resolution_clock::now();

    init_memory(total_mb);

    std::cout << std::endl << "Init done" << std::endl;

    if (early_stop) {
        return 0;
    }

    std::vector<std::thread> threads;
    for (int i = 0; i < num_threads; ++i) {
        if (pin_cpu && intentional_remote && !(i%2))
            continue;

        threads.emplace_back(memory_intensive_task, i, total_mb, rounds);

        if (pin_cpu) {
            // Pin thread to a specific CPU core
            cpu_set_t cpuset;
            CPU_ZERO(&cpuset);
            CPU_SET(i, &cpuset); // Pin to node 0 and 1
            int rc = pthread_setaffinity_np(threads.back().native_handle(), sizeof(cpu_set_t), &cpuset);
            if (rc != 0) {
                std::cerr << "Error calling pthread_setaffinity_np: " << rc << "\n";
            }
        }
    }

    for (auto& t : threads) {
        t.join();
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end_time - start_time;
    std::cout << "Benchmark finished in " << elapsed.count() << " seconds." << std::endl;

    if (memory_block != nullptr) {
        delete memory_block;
        memory_block = nullptr;
    }

    return 0;
}
