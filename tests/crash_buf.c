#include <stdio.h>
int main(int argc, char *argv[])
{
	FILE *fd;
	char buffer[32];
	size_t bytes_read;
	fd = fopen(argv[1], "rb");
	char *ptr = buffer;
	while (!feof(fd)) {
		bytes_read = fread(ptr, 1, 1, fd);
		if (bytes_read == 0) break;
		ptr += 1;
	}
	printf("File: %s", buffer);
	return 0;
}
