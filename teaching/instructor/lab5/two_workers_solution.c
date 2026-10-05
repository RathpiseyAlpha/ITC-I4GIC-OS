/* Public preparation model. Each worker owns one result field. */
#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

struct job { int id; int steps; int result; };

static void *worker(void *arg) {
    struct job *job = arg;
    for (int step = 0; step < job->steps; ++step) {
        job->result += job->id;
        struct timespec delay = {0, 20000000};
        nanosleep(&delay, NULL); /* demonstration delay, not synchronization */
    }
    printf("worker %d finished\n", job->id);
    return NULL;
}

int main(void) {
    struct job jobs[2] = {{2, 3, 0}, {3, 4, 0}};
    pthread_t threads[2];
    int created = 0, failed = 0;
    for (int i = 0; i < 2; ++i) {
        int rc = pthread_create(&threads[i], NULL, worker, &jobs[i]);
        if (rc != 0) {
            fprintf(stderr, "create worker %d: %s\n", jobs[i].id, strerror(rc));
            failed = 1;
            break;
        }
        ++created;
    }
    for (int i = 0; i < created; ++i) {
        int rc = pthread_join(threads[i], NULL);
        if (rc != 0) {
            fprintf(stderr, "join worker %d: %s\n", jobs[i].id, strerror(rc));
            failed = 1;
        } else {
            printf("%c result=%d\n", 'A' + i, jobs[i].result);
        }
    }
    return failed;
}
