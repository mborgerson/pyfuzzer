#include <stdio.h>
#include <string.h>

int loop_a_bunch()
{
    int x = 20;
    for (volatile int i = 0; i < 1000; i++) {
        x += 1;
    }

    return x;
}

int do_crash()
{
    *(volatile char *)(0x123) = 5;
    return 0;
}

int main(int argc, char *argv[])
{
    if (argc < 2) return 1;
    FILE *fd = fopen(argv[1], "rb");
    char buf[40];
    fseek(fd, 0, SEEK_END);
    size_t len = ftell(fd);
    fseek(fd, 0, SEEK_SET);
    fread(buf, 1, len, fd);
    if (strcmp(buf, "Hello Worl\xE4") == 0) {
        loop_a_bunch();
    }
    if (strcmp(buf, "Hell\xEF World") == 0) {
        do_crash();
    }
    printf("%s\n", buf);
    return 0;    
}