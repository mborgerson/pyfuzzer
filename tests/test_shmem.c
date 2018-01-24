#define MAP_SIZE (64*1024)
#define SHM_ENV_VAR "__AFL_SHM_ID"
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/shm.h>

int main(int argc, char *argv[])
{
    char *id_str = getenv(SHM_ENV_VAR);
    int shm_id;

    if (id_str == NULL) {
        fprintf(stderr, "Env var %s not defined!\n", SHM_ENV_VAR);
        return 1;
    }

    shm_id = atoi(id_str);
    char *buf = shmat(shm_id, NULL, 0);

    if (buf == (void*)-1) {
        fprintf(stderr, "shmat returned -1\n");
        exit(1);
    }

    for (int i = 0; i < MAP_SIZE; i++) {
        buf[i] = i & 0xff;
    }

    return 0;
}
