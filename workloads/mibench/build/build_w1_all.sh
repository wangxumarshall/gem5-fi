#!/bin/bash
# build_w1_all.sh — W1 单进程多 main 十件套构建（v2，fork-free 设计）
# 用法：cd workloads/mibench && bash build/build_w1_all.sh
set -e
P=/tmp/mibench_probe
W=$(cd "$(dirname "$0")/.." && pwd)
B=$W/build/objs
mkdir -p $B
CC="gcc -O2 -w"

echo "=== 1. bf（blowfish） ==="
$CC -Dmain=bm_bf_main -c -o $B/bf.o $W/build/bf/bf.c
for f in bf_cbc bf_cfb64 bf_ecb bf_enc bf_ofb64 bf_skey; do
    $CC -c -o $B/${f}.o $P/security/blowfish/${f}.c
done

echo "=== 2. patricia ==="
$CC -Dmain=bm_patricia_main -I$P/network/patricia -c -o $B/pat.o $W/build/patricia/patricia_test.c
$CC -I$P/network/patricia -c -o $B/pat_impl.o $P/network/patricia/patricia.c

echo "=== 3. fft ==="
$CC -Dmain=bm_fft_main -c -o $B/fft.o $P/telecomm/FFT/main.c
$CC -c -o $B/fft_f.o $P/telecomm/FFT/fourierf.c
$CC -c -o $B/fft_m.o $P/telecomm/FFT/fftmisc.c

echo "=== 4. gsm（toast/untoast，argv[0] 判定行为） ==="
GSMF="-DSASR -DSTUPID_COMPILER -DNeedFunctionPrototypes=1 -I$P/telecomm/gsm/inc"
for f in $P/telecomm/gsm/src/*.c; do
    b=$(basename $f .c)
    if [ "$b" = "toast" ]; then
        $CC $GSMF -Dmain=bm_gsm_main -c -o $B/gsm_toast.o $f
    else
        $CC $GSMF -c -o $B/gsm_$b.o $f
    fi
done

echo "=== 5. dijkstra ==="
$CC -Dmain=bm_dijkstra_main -c -o $B/dij.o $P/network/dijkstra/dijkstra_large.c

echo "=== 6. rijndael（ftell 补丁版） ==="
$CC -Dmain=bm_rijndael_main -I$W/build/rijndael -c -o $B/rnd.o $W/build/rijndael/aesxam.c
$CC -I$W/build/rijndael -c -o $B/rnd_impl.o $W/build/rijndael/aes.c

echo "=== 7. sha（LONG=uint32 + LE 补丁版） ==="
$CC -DLITTLE_ENDIAN -Dmain=bm_sha_main -I$W/build/sha -c -o $B/sha.o $W/build/sha/sha_driver.c
$CC -DLITTLE_ENDIAN -I$W/build/sha -c -o $B/sha_impl.o $W/build/sha/sha.c

echo "=== 8. bitcount（Bits-only 补丁版） ==="
$CC -Dmain=bm_bitcount_main -I$W/build/bitcount -c -o $B/bc.o $W/build/bitcount/bitcnts.c
for f in bitarray bitcnt_1 bitcnt_2 bitcnt_3 bitcnt_4 bitstrng bstr_i; do
    $CC -I$W/build/bitcount -c -o $B/bc_${f}.o $W/build/bitcount/${f}.c
done

echo "=== 9. susan（edge=-e / smooth=-s 双模式） ==="
$CC -Dmain=bm_susan_main -c -o $B/sus.o $P/automotive/susan/susan.c

echo "=== 10. 驱动器 + 链接 ==="
$CC -c -o $B/w1_all.o $W/build/w1_all.c
gcc -static -Wl,--wrap=exit -o $W/bin/w1_all $B/*.o -lm
echo "=== 完成：$W/bin/w1_all ==="
ls -la $W/bin/w1_all
