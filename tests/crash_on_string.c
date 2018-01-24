#include <stdio.h>
#include <string.h>

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
    if (strcmp(buf, "Hello\x21World") == 0) {
        do_crash();
    }
    printf("%s\n", buf);
    return 0;    
}