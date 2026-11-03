/*
 * gem5fi_oracle.h — PolyBench output-array dump for the FSU element oracle.
 *
 * Opt-in, byte-exact serialisation of one live-out array.  When neither
 *   --array-dump=<path>            (last occurrence on argv wins)
 *   POLYBENCH_ARRAY_DUMP=<path>    (environment variable)
 * is present, every function here is a no-op: stdout, the FINAL=<16hex>
 * line and the program's exit behaviour are completely unchanged.
 *
 * Canonical on-disk format
 *   * raw elements, no header, no separators;
 *   * row-major order (the caller decides which elements belong to the
 *     output domain via gem5fi_oracle_dump_*_from_argv);
 *   * every element is written little-endian, least-significant byte
 *     first, independent of the host's byte order;
 *   * fp32 = elem_size 4, fp64 = elem_size 8.  elem_size 1..8 is
 *     supported; anything larger is rejected.
 *
 * On success one line is printed on stdout:
 *   ARRAY_DUMP path=<p> count=<n> elem_size=<s> fnv1a=<16hex>
 * where fnv1a is FNV-1a 64 (offset basis 0xcbf29ce484222325, prime
 * 0x100000001b3) over exactly the bytes written to the file.
 *
 * SHA-256 is deliberately NOT implemented here: tools/fsu_oracle.py hashes
 * the saved bytes on the host side, so there is exactly one hashing
 * implementation and the C dump stays dependency-free.
 *
 * This header is shared by the five W5 PolyBench kernels and by
 * tests/unit/fsu_oracle_dump_test.c; every function is static inline so
 * including it from several translation units is safe.
 *
 * GEM5FI_ORACLE_HOST_IS_LITTLE_ENDIAN is a *test-only* override: the host
 * unit test defines it to 0 and feeds explicitly big-endian element bytes
 * to exercise the big-endian conversion path on a little-endian host.  Do
 * not define it in production builds.
 */
#ifndef GEM5FI_POLYBENCH_ORACLE_H
#define GEM5FI_POLYBENCH_ORACLE_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define GEM5FI_ORACLE_ARG_PREFIX "--array-dump="
#define GEM5FI_ORACLE_ENV        "POLYBENCH_ARRAY_DUMP"

/* Host byte order probe (overridable only for the host unit test). */
#ifndef GEM5FI_ORACLE_HOST_IS_LITTLE_ENDIAN
static inline int gem5fi_oracle_host_is_little_endian(void)
{
  const uint16_t probe = 1u;
  return *((const unsigned char *) &probe) == 1u;
}
#else
static inline int gem5fi_oracle_host_is_little_endian(void)
{
  return (GEM5FI_ORACLE_HOST_IS_LITTLE_ENDIAN) ? 1 : 0;
}
#endif

/* Return the dump path, or NULL when dumping was not requested.
 *
 * Precedence (deliberate, no silent fallback):
 *   * if ANY argv entry starts with --array-dump=, the LAST such entry is
 *     authoritative; an empty value means "no dump" and the environment
 *     variable is NOT consulted;
 *   * otherwise POLYBENCH_ARRAY_DUMP is used;
 *   * an empty environment value also means "no dump". */
static inline const char *gem5fi_oracle_path_from_argv(int argc, char **argv)
{
  const char *path = NULL;
  const size_t prefix_len = sizeof(GEM5FI_ORACLE_ARG_PREFIX) - 1;
  int i;

  if (argv != NULL)
    for (i = 1; i < argc; i++)
      if (argv[i] != NULL &&
          strncmp(argv[i], GEM5FI_ORACLE_ARG_PREFIX, prefix_len) == 0)
        path = argv[i] + prefix_len;

  if (path == NULL)
    path = getenv(GEM5FI_ORACLE_ENV);

  if (path == NULL || path[0] == '\0')
    return NULL;
  return path;
}

/* Convert one element to canonical little-endian bytes, independent of
 * the host's byte order.  Returns 0 on success, -1 on invalid arguments. */
static inline int gem5fi_oracle_elem_le_bytes(const void *elem,
                                              unsigned long elem_size,
                                              unsigned char out[8])
{
  const unsigned char *p = (const unsigned char *) elem;
  uint64_t v = 0;
  unsigned long i;

  if (elem == NULL || out == NULL || elem_size == 0 || elem_size > 8)
    return -1;

  if (gem5fi_oracle_host_is_little_endian())
    for (i = 0; i < elem_size; i++)
      v |= ((uint64_t) p[i]) << (8u * i);
  else
    for (i = 0; i < elem_size; i++)
      v = (v << 8) | (uint64_t) p[i];

  for (i = 0; i < elem_size; i++)
    out[i] = (unsigned char) ((v >> (8u * i)) & 0xffu);
  return 0;
}

/* Streaming dump writer. */
typedef struct {
  FILE *file;
  const char *path;
  unsigned long count;
  unsigned long elem_size;
  uint64_t fnv1a;
  int failed;
} gem5fi_oracle_writer;

static inline int gem5fi_oracle_writer_begin(gem5fi_oracle_writer *w,
                                              const char *path,
                                              unsigned long elem_size)
{
  if (w == NULL || path == NULL || path[0] == '\0' ||
      elem_size == 0 || elem_size > 8) {
    fprintf(stderr, "gem5fi_oracle: invalid dump request\n");
    return -1;
  }
  w->file = fopen(path, "wb");
  w->path = path;
  w->count = 0;
  w->elem_size = elem_size;
  w->fnv1a = 0xcbf29ce484222325ULL;
  w->failed = 0;
  if (w->file == NULL) {
    fprintf(stderr, "gem5fi_oracle: cannot open dump path=%s\n", path);
    return -1;
  }
  return 0;
}

static inline int gem5fi_oracle_writer_add(gem5fi_oracle_writer *w,
                                            const void *elem)
{
  unsigned char le[8];
  unsigned long i;

  if (w == NULL || w->file == NULL || w->failed)
    return -1;
  if (gem5fi_oracle_elem_le_bytes(elem, w->elem_size, le) != 0) {
    w->failed = 1;
    return -1;
  }
  if (fwrite(le, 1, w->elem_size, w->file) != w->elem_size) {
    w->failed = 1;
    return -1;
  }
  for (i = 0; i < w->elem_size; i++) {
    w->fnv1a ^= (uint64_t) le[i];
    w->fnv1a *= 0x100000001b3ULL;
  }
  w->count++;
  return 0;
}

/* Close the file; print the ARRAY_DUMP line only if every byte was
 * written.  Returns 0 on success (including "no dump requested" handled
 * by the callers), -1 on failure. */
static inline int gem5fi_oracle_writer_finish(gem5fi_oracle_writer *w)
{
  if (w == NULL)
    return -1;
  if (w->file != NULL) {
    if (fclose(w->file) != 0)
      w->failed = 1;
    w->file = NULL;
  }
  if (w->failed) {
    fprintf(stderr, "gem5fi_oracle: dump failed path=%s\n",
            w->path != NULL ? w->path : "(null)");
    return -1;
  }
  printf("ARRAY_DUMP path=%s count=%lu elem_size=%lu fnv1a=%016llx\n",
         w->path, w->count, w->elem_size,
         (unsigned long long) w->fnv1a);
  return 0;
}

/* Dump `count` contiguous elements starting at `base` (row-major).
 * No-op (returns 0, writes nothing) when no dump path was requested. */
static inline int gem5fi_oracle_dump_from_argv(int argc, char **argv,
                                                const void *base,
                                                unsigned long count,
                                                unsigned long elem_size)
{
  const char *path = gem5fi_oracle_path_from_argv(argc, argv);
  gem5fi_oracle_writer w;
  unsigned long i;

  if (path == NULL)
    return 0;
  if (base == NULL && count != 0) {
    fprintf(stderr, "gem5fi_oracle: NULL array with count=%lu\n", count);
    return -1;
  }
  if (gem5fi_oracle_writer_begin(&w, path, elem_size) != 0)
    return -1;
  for (i = 0; i < count; i++)
    if (gem5fi_oracle_writer_add(&w,
            (const unsigned char *) base + i * elem_size) != 0) {
      w.failed = 1;
      return gem5fi_oracle_writer_finish(&w);
    }
  return gem5fi_oracle_writer_finish(&w);
}

/* Dump the lower triangle INCLUDING the diagonal of an n x n row-major
 * matrix, in row-major order: (0,0), (1,0), (1,1), (2,0), ... (n-1,n-1).
 * This is the exact FINAL domain of PolyBench cholesky. */
static inline int gem5fi_oracle_dump_lower_from_argv(int argc, char **argv,
                                                      const void *base,
                                                      unsigned long n,
                                                      unsigned long elem_size)
{
  const char *path = gem5fi_oracle_path_from_argv(argc, argv);
  gem5fi_oracle_writer w;
  unsigned long i, j;

  if (path == NULL)
    return 0;
  if (base == NULL && n != 0) {
    fprintf(stderr, "gem5fi_oracle: NULL matrix with n=%lu\n", n);
    return -1;
  }
  if (gem5fi_oracle_writer_begin(&w, path, elem_size) != 0)
    return -1;
  for (i = 0; i < n; i++)
    for (j = 0; j <= i; j++)
      if (gem5fi_oracle_writer_add(&w,
              (const unsigned char *) base +
              (i * n + j) * elem_size) != 0) {
        w.failed = 1;
        return gem5fi_oracle_writer_finish(&w);
      }
  return gem5fi_oracle_writer_finish(&w);
}

#endif /* GEM5FI_POLYBENCH_ORACLE_H */
