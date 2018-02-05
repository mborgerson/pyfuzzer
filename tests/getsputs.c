#include <stdlib.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char *argv[])
{
    char buf[32];
    memset(buf, 0, sizeof(buf));
    fgets(buf, sizeof(buf), stdin);
    puts(buf);
    return 0;
}
