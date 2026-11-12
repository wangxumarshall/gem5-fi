// mmu_install.c — boot-time installer + checkpoint dispatcher.
//
// Served by `m5 readfile`; /root/gem5_init.sh writes it to /tmp/script and
// executes it.  It writes /root/mmu_w9 and /root/mmu_w10 from embedded blobs,
// takes a checkpoint, then reads the CURRENT run's --readfile payload:
//   * boot pass: the payload is this ELF again -> exit (checkpoint is saved);
//   * restore pass: the payload is a shell script starting with "#!" ->
//     exec /bin/sh on it (W9/W10 rcS).
//
// This avoids taking the checkpoint inside a shell `if` (which would resume
// after the branch and skip the restore dispatch).
//
// Build (from workloads/mmu):
//   ld -r -b binary -o install/w9_blob.o W9/mmu_w9
//   ld -r -b binary -o install/w10_blob.o W10/mmu_w10
//   gcc -O2 -static -o install/mmu_install install/mmu_install.c \
//       install/w9_blob.o install/w10_blob.o
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

extern const unsigned char _binary_W9_mmu_w9_start[];
extern const unsigned char _binary_W9_mmu_w9_end[];
extern const unsigned char _binary_W10_mmu_w10_start[];
extern const unsigned char _binary_W10_mmu_w10_end[];

static int
write_file(const char *path, const unsigned char *data, size_t len, mode_t mode)
{
    int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, mode);
    if (fd < 0) {
        fprintf(stderr, "[mmu-install] open %s: %s\n", path, strerror(errno));
        return -1;
    }
    size_t off = 0;
    while (off < len) {
        ssize_t n = write(fd, data + off, len - off);
        if (n <= 0) {
            fprintf(stderr, "[mmu-install] write %s: %s\n", path,
                    strerror(errno));
            close(fd);
            return -1;
        }
        off += (size_t)n;
    }
    if (fchmod(fd, mode) != 0)
        fprintf(stderr, "[mmu-install] chmod %s: %s\n", path, strerror(errno));
    fsync(fd);
    close(fd);
    return 0;
}

static int
starts_with_shebang(const char *path)
{
    char b[2] = {0, 0};
    int fd = open(path, O_RDONLY);
    if (fd < 0)
        return 0;
    ssize_t n = read(fd, b, 2);
    close(fd);
    return n == 2 && b[0] == '#' && b[1] == '!';
}

int
main(void)
{
    size_t w9_len = (size_t)(_binary_W9_mmu_w9_end - _binary_W9_mmu_w9_start);
    size_t w10_len = (size_t)(_binary_W10_mmu_w10_end - _binary_W10_mmu_w10_start);
    printf("[mmu-install] w9=%zu w10=%zu\n", w9_len, w10_len);
    fflush(stdout);

    if (write_file("/root/mmu_w9", _binary_W9_mmu_w9_start, w9_len, 0755) ||
        write_file("/root/mmu_w10", _binary_W10_mmu_w10_start, w10_len, 0755))
        return 2;

    int dfd = open("/root", O_RDONLY | O_DIRECTORY);
    if (dfd >= 0) {
        fsync(dfd);
        close(dfd);
    }

    printf("[mmu-install] taking checkpoint\n");
    fflush(stdout);
    int rc = system("m5 checkpoint");
    printf("[mmu-install] checkpoint rc=%d; reading payload\n", rc);
    fflush(stdout);
    rc = system("m5 readfile > /tmp/next.sh");
    printf("[mmu-install] readfile rc=%d\n", rc);
    fflush(stdout);

    if (!starts_with_shebang("/tmp/next.sh")) {
        printf("[mmu-install] boot pass (payload is not a shell script); "
               "exiting\n");
        fflush(stdout);
        system("m5 exit");
        return 0;
    }

    printf("[mmu-install] restore pass; exec payload\n");
    fflush(stdout);
    execl("/bin/sh", "sh", "/tmp/next.sh", (char *)NULL);
    fprintf(stderr, "[mmu-install] exec failed: %s\n", strerror(errno));
    return 2;
}
