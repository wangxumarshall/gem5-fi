/*
 * Tiny host unit test for workloads/ooo/polybench/utilities/gem5fi_oracle.h.
 *
 * Build (from the repo root):
 *   gcc -O0 -Wall -Wextra -I workloads/ooo/polybench/utilities \
 *       -o /tmp/fsu_oracle_dump_test tests/unit/fsu_oracle_dump_test.c
 *
 * Modes (all still honour --array-dump=<path> / POLYBENCH_ARRAY_DUMP):
 *   (default)              dump 9 contiguous fp32-sized elements
 *                          (0x01020304, 0xa1b2c3d4, ...)
 *   --lower                dump the lower triangle incl. diagonal of a 3x3
 *                          matrix (6 elements, row-major)
 *   --big-endian-input     dump the same 9 values, but the input bytes are
 *                          deliberately stored big-endian.  Build with
 *                          -DGEM5FI_ORACLE_HOST_IS_LITTLE_ENDIAN=0 so the
 *                          header exercises its big-endian conversion path
 *                          even though the host is little-endian.
 *
 * The test writes no FINAL line; it exists only to verify the dump bytes,
 * the FNV-1a line and the no-path no-op behaviour from Python.
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include <gem5fi_oracle.h>

static uint32_t flat[9] = {
  0x01020304u, 0xa1b2c3d4u, 0x0f0e0d0cu,
  0x11223344u, 0x55667788u, 0x99aabbccu,
  0xdeadbeefu, 0xcafebabeu, 0x12345678u
};

/* Same numeric values as `flat`, stored one byte per element byte in
 * big-endian order: big[0] = {0x01,0x02,0x03,0x04}, etc. */
static unsigned char big[9][4] = {
  {0x01, 0x02, 0x03, 0x04},
  {0xa1, 0xb2, 0xc3, 0xd4},
  {0x0f, 0x0e, 0x0d, 0x0c},
  {0x11, 0x22, 0x33, 0x44},
  {0x55, 0x66, 0x77, 0x88},
  {0x99, 0xaa, 0xbb, 0xcc},
  {0xde, 0xad, 0xbe, 0xef},
  {0xca, 0xfe, 0xba, 0xbe},
  {0x12, 0x34, 0x56, 0x78}
};

int main(int argc, char **argv)
{
  int lower = 0;
  int big_endian_input = 0;
  int i;

  for (i = 1; i < argc; i++) {
    if (strcmp(argv[i], "--lower") == 0)
      lower = 1;
    if (strcmp(argv[i], "--big-endian-input") == 0)
      big_endian_input = 1;
  }

  if (lower)
    return gem5fi_oracle_dump_lower_from_argv(
               argc, argv, flat, 3, sizeof(flat[0])) == 0 ? 0 : 1;

  if (big_endian_input)
    return gem5fi_oracle_dump_from_argv(
               argc, argv, big, 9, sizeof(big[0])) == 0 ? 0 : 1;

  return gem5fi_oracle_dump_from_argv(
             argc, argv, flat, 9, sizeof(flat[0])) == 0 ? 0 : 1;
}
