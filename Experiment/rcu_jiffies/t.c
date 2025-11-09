// t.c  —— 让某个 CPU 20s 保持 SCHED_FIFO 忙循环
// gcc -O2 -pthread t.c -o t

#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <time.h>
#include <unistd.h>

void *hog(void *arg){
  cpu_set_t cs; CPU_ZERO(&cs); CPU_SET((long)arg, &cs);
  pthread_setaffinity_np(pthread_self(), sizeof(cs), &cs);
  struct sched_param sp = { .sched_priority = 98 };
  pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp); // 需 root 或 CAP_SYS_NICE
  volatile unsigned long long x=0, end = (unsigned long long)time(NULL)+20;
  while ((unsigned long long)time(NULL) < end) x++;
  return NULL;
}
int main(){ pthread_t th; pthread_create(&th, NULL, hog, (void*)0L); pthread_join(th, NULL); }