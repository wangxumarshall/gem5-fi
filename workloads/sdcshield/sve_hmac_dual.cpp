/* sve_hmac_dual.cpp — TRUE same-source dual-channel validation of the
 * sdcshield ipsec HMAC layer (PR #284 review round 2, local-claude
 * Important-1: the P4 gem5 evidence载体 sve_sha_dual.c was a MIRRORED copy
 * of the kernels — this harness instead #includes the repository's ACTUAL
 * headers, tests/cpu/sve/ipsec/sve_hmac.h (+ sve_sha_kernels.h), so the
 * machine code under test is the same source the 17 ipsec tests compile
 * against).
 *
 * What runs per tier:
 *   1. VL gate mirroring verify.cpp (svcntw in [4,32], svcntd in [2,16];
 *      exit 3 otherwise) + the glue invariant the 17 tests' init relies on
 *      (nstreams = svl/4 == svcntw(), svl/8 == svcntd()).
 *   2. RFC 2202/4231 known-answer vectors (python3-hmac-verified hex,
 *      generated on the x3b-class host 2026-10-25) on ALL streams at once —
 *      anchors BOTH the scalar oracle and the SVE path to published values.
 *   3. Per-stream distinct keys/messages over in-bound lengths spanning the
 *      assembly boundary (1900/1830 knob caps, exact max 1975/1903, 0/1,
 *      block-straddlers) — per-stream byte-exact SVE-vs-oracle compare.
 *   4. Guard probes (the PR's own safety code, first execution ever):
 *      msg_len over-boundary (1976/1904), far (2048/65536/SIZE_MAX/2) and
 *      the WRAP probes (size_t)-64/(size_t)-63 — near-SIZE_MAX msg_len
 *      values whose body=64/128+msg_len wraps to 0/1 and would slip past
 *      the old post-hoc padded check into a huge memcpy; every probe MUST
 *      return -1 before touching the buffers. key_len over-block (65/129,
 *      1000) likewise.
 *
 * Channels: A = per-stream byte-exact digest compare vs the independent
 *           scalar oracle (FIPS-standard algorithm code; K/IV tables reused
 *           from the included repo header — same-source constants, no
 *           hand-retyping);
 *           B = FNV-1a over every SVE digest word.
 * argv: [fixed|random] [seed]; exit 0 / 1 (fails) / 3 (unsupported VL).
 * Build: clang++ -static -O2 -march=armv9-a+sve -Wall -Wextra \
 *          -I<sdcshield>/tests/cpu/sve/ipsec -o sve_hmac_dual \
 *          sve_hmac_dual.cpp
 * Run:   gem5.opt configs/se/arm_chaos.py --cpu O3 --cmd \
 *          workloads/sdcshield/sve_hmac_dual --sve_vl 8 \
 *          --workload_args "random 2"
 */
#include "sve_hmac.h"   /* the REAL repository header (same-source) */
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>

/* ---- RNG (fixed mode uses closed-form patterns; random mode xorshift32) ---- */
static uint32_t xs_state;
static uint32_t xs32(void)
{
    xs_state ^= xs_state << 13;
    xs_state ^= xs_state >> 17;
    xs_state ^= xs_state << 5;
    return xs_state;
}
static int g_random = 0;
static uint8_t byte_at(int s, size_t i, int which)
{
    if (g_random)
        return (uint8_t)xs32();
    return (uint8_t)(s * (which ? 89 : 41) + (int)i * (which ? 13 : 7));
}

static unsigned g_fails = 0;
static uint64_t fnv = 1469598103934665603ULL;
static void fnv_bits(const void *p, size_t n)
{
    const uint8_t *b = (const uint8_t *)p;
    for (size_t i = 0; i < n; ++i) {
        fnv ^= b[i];
        fnv *= 1099511628211ULL;
    }
}
static void check(int cond, const char *what)
{
    if (!cond) {
        ++g_fails;
        if (g_fails <= 20)
            printf("MISMATCH: %s\n", what);
    }
}

/* ---- independent scalar oracle (FIPS algorithm code; K/IV tables come from
 * the included repository header — published FIPS constants, no retyping) ---- */
static uint32_t rotr32(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }
static uint64_t rotr64(uint64_t x, int n) { return (x >> n) | (x << (64 - n)); }
static uint32_t rotl32(uint32_t x, int n) { return (x << n) | (x >> (32 - n)); }

static void sha256_block_scalar(uint32_t st[8], const uint8_t *blk)
{
    uint32_t w[64];
    for (int t = 0; t < 16; ++t)
        w[t] = ((uint32_t)blk[4*t] << 24) | ((uint32_t)blk[4*t+1] << 16) |
               ((uint32_t)blk[4*t+2] << 8) | (uint32_t)blk[4*t+3];
    for (int t = 16; t < 64; ++t) {
        uint32_t s0 = rotr32(w[t-15], 7) ^ rotr32(w[t-15], 18) ^ (w[t-15] >> 3);
        uint32_t s1 = rotr32(w[t-2], 17) ^ rotr32(w[t-2], 19) ^ (w[t-2] >> 10);
        w[t] = w[t-16] + s0 + w[t-7] + s1;
    }
    uint32_t a = st[0], b = st[1], c = st[2], d = st[3];
    uint32_t e = st[4], f = st[5], g = st[6], h = st[7];
    for (int t = 0; t < 64; ++t) {
        uint32_t S1 = rotr32(e, 6) ^ rotr32(e, 11) ^ rotr32(e, 25);
        uint32_t ch = (e & f) ^ (~e & g);
        uint32_t t1 = h + S1 + ch + sha256_k[t] + w[t];
        uint32_t S0 = rotr32(a, 2) ^ rotr32(a, 13) ^ rotr32(a, 22);
        uint32_t mj = (a & b) ^ (a & c) ^ (b & c);
        uint32_t t2 = S0 + mj;
        h = g; g = f; f = e; e = d + t1;
        d = c; c = b; b = a; a = t1 + t2;
    }
    st[0] += a; st[1] += b; st[2] += c; st[3] += d;
    st[4] += e; st[5] += f; st[6] += g; st[7] += h;
}

static void sha2_32_digest(const uint8_t *msg, size_t len, uint32_t out[8],
                           const uint32_t iv[8])
{
    uint32_t st[8];
    for (int i = 0; i < 8; ++i) st[i] = iv[i];
    size_t total = ((len + 9 + 63) / 64) * 64;
    uint8_t buf[2112];
    memcpy(buf, msg, len);
    memset(buf + len, 0, total - len);
    buf[len] = 0x80;
    uint64_t bits = (uint64_t)len * 8;
    for (int i = 0; i < 8; ++i)
        buf[total - 1 - i] = (uint8_t)(bits >> (8 * i));
    for (size_t off = 0; off < total; off += 64)
        sha256_block_scalar(st, buf + off);
    for (int i = 0; i < 8; ++i) out[i] = st[i];
}

static void sha512_block_scalar(uint64_t st[8], const uint8_t *blk)
{
    uint64_t w[80];
    for (int t = 0; t < 16; ++t) {
        uint64_t x = 0;
        for (int k = 0; k < 8; ++k)
            x = (x << 8) | blk[8*t + k];
        w[t] = x;
    }
    for (int t = 16; t < 80; ++t) {
        uint64_t s0 = rotr64(w[t-15], 1) ^ rotr64(w[t-15], 8) ^ (w[t-15] >> 7);
        uint64_t s1 = rotr64(w[t-2], 19) ^ rotr64(w[t-2], 61) ^ (w[t-2] >> 6);
        w[t] = w[t-16] + s0 + w[t-7] + s1;
    }
    uint64_t a = st[0], b = st[1], c = st[2], d = st[3];
    uint64_t e = st[4], f = st[5], g = st[6], h = st[7];
    for (int t = 0; t < 80; ++t) {
        uint64_t S1 = rotr64(e, 14) ^ rotr64(e, 18) ^ rotr64(e, 41);
        uint64_t ch = (e & f) ^ (~e & g);
        uint64_t t1 = h + S1 + ch + sha512_k[t] + w[t];
        uint64_t S0 = rotr64(a, 28) ^ rotr64(a, 34) ^ rotr64(a, 39);
        uint64_t mj = (a & b) ^ (a & c) ^ (b & c);
        uint64_t t2 = S0 + mj;
        h = g; g = f; f = e; e = d + t1;
        d = c; c = b; b = a; a = t1 + t2;
    }
    st[0] += a; st[1] += b; st[2] += c; st[3] += d;
    st[4] += e; st[5] += f; st[6] += g; st[7] += h;
}

static void sha2_64_digest(const uint8_t *msg, size_t len, uint64_t out[8],
                           const uint64_t iv[8])
{
    uint64_t st[8];
    for (int i = 0; i < 8; ++i) st[i] = iv[i];
    size_t total = ((len + 17 + 127) / 128) * 128;
    uint8_t buf[2176];
    memcpy(buf, msg, len);
    memset(buf + len, 0, total - len);
    buf[len] = 0x80;
    uint64_t bits = (uint64_t)len * 8;
    /* 128-bit length field: high 8 bytes stay zero (memset), low 8 big-endian */
    for (int i = 0; i < 8; ++i)
        buf[total - 1 - i] = (uint8_t)(bits >> (8 * i));
    for (size_t off = 0; off < total; off += 128)
        sha512_block_scalar(st, buf + off);
    for (int i = 0; i < 8; ++i) out[i] = st[i];
}

static const uint32_t sha1_iv_s[5] =
    {0x67452301u, 0xefcdab89u, 0x98badcfeu, 0x10325476u, 0xc3d2e1f0u};

static void sha1_block_scalar(uint32_t st[5], const uint8_t *blk)
{
    uint32_t w[80];
    for (int t = 0; t < 16; ++t)
        w[t] = ((uint32_t)blk[4*t] << 24) | ((uint32_t)blk[4*t+1] << 16) |
               ((uint32_t)blk[4*t+2] << 8) | (uint32_t)blk[4*t+3];
    for (int t = 16; t < 80; ++t)
        w[t] = rotl32(w[t-3] ^ w[t-8] ^ w[t-14] ^ w[t-16], 1);
    uint32_t a = st[0], b = st[1], c = st[2], d = st[3], e = st[4];
    for (int t = 0; t < 80; ++t) {
        uint32_t f, k;
        if (t < 20)      { f = (b & c) | (~b & d);            k = 0x5a827999u; }
        else if (t < 40) { f = b ^ c ^ d;                     k = 0x6ed9eba1u; }
        else if (t < 60) { f = (b & c) | (b & d) | (c & d);   k = 0x8f1bbcdcu; }
        else             { f = b ^ c ^ d;                     k = 0xca62c1d6u; }
        uint32_t tmp = rotl32(a, 5) + f + e + k + w[t];
        e = d; d = c; c = rotl32(b, 30); b = a; a = tmp;
    }
    st[0] += a; st[1] += b; st[2] += c; st[3] += d; st[4] += e;
}

static void sha1_digest(const uint8_t *msg, size_t len, uint32_t out[5])
{
    uint32_t st[5];
    for (int i = 0; i < 5; ++i) st[i] = sha1_iv_s[i];
    size_t total = ((len + 9 + 63) / 64) * 64;
    uint8_t buf[2112];
    memcpy(buf, msg, len);
    memset(buf + len, 0, total - len);
    buf[len] = 0x80;
    uint64_t bits = (uint64_t)len * 8;
    for (int i = 0; i < 8; ++i)
        buf[total - 1 - i] = (uint8_t)(bits >> (8 * i));
    for (size_t off = 0; off < total; off += 64)
        sha1_block_scalar(st, buf + off);
    for (int i = 0; i < 5; ++i) out[i] = st[i];
}

/* HMAC per RFC 2104 on the scalar oracle. inner_bytes = the family's digest
 * size in bytes (what the outer hash consumes: 20/28/32/48/64). */
static void hmac_sha1_scalar(const uint8_t *key, size_t key_len,
                             const uint8_t *msg, size_t msg_len, uint8_t out[20])
{
    uint8_t k[64];
    memset(k, 0, 64);
    memcpy(k, key, key_len);
    uint8_t inner[64 + 2048];
    for (int i = 0; i < 64; ++i) inner[i] = k[i] ^ 0x36;
    memcpy(inner + 64, msg, msg_len);
    uint32_t ist[5];
    sha1_digest(inner, 64 + msg_len, ist);
    uint8_t outer[64 + 20];
    for (int i = 0; i < 64; ++i) outer[i] = k[i] ^ 0x5c;
    for (int w = 0; w < 5; ++w) {
        outer[64 + 4*w + 0] = (uint8_t)(ist[w] >> 24);
        outer[64 + 4*w + 1] = (uint8_t)(ist[w] >> 16);
        outer[64 + 4*w + 2] = (uint8_t)(ist[w] >> 8);
        outer[64 + 4*w + 3] = (uint8_t)(ist[w]);
    }
    uint32_t ost[5];
    sha1_digest(outer, 64 + 20, ost);
    for (int w = 0; w < 5; ++w) {
        out[4*w + 0] = (uint8_t)(ost[w] >> 24);
        out[4*w + 1] = (uint8_t)(ost[w] >> 16);
        out[4*w + 2] = (uint8_t)(ost[w] >> 8);
        out[4*w + 3] = (uint8_t)(ost[w]);
    }
}

static void hmac_fam32_scalar(const uint8_t *key, size_t key_len,
                              const uint8_t *msg, size_t msg_len,
                              uint8_t *out, size_t inner_bytes, size_t out_words,
                              const uint32_t iv[8])
{
    uint8_t k[64];
    memset(k, 0, 64);
    memcpy(k, key, key_len);
    uint8_t inner[64 + 2048];
    for (int i = 0; i < 64; ++i) inner[i] = k[i] ^ 0x36;
    memcpy(inner + 64, msg, msg_len);
    uint32_t ist[8];
    sha2_32_digest(inner, 64 + msg_len, ist, iv);
    uint8_t outer[64 + 32];
    for (int i = 0; i < 64; ++i) outer[i] = k[i] ^ 0x5c;
    for (size_t w = 0; w < inner_bytes / 4; ++w) {
        outer[64 + 4*w + 0] = (uint8_t)(ist[w] >> 24);
        outer[64 + 4*w + 1] = (uint8_t)(ist[w] >> 16);
        outer[64 + 4*w + 2] = (uint8_t)(ist[w] >> 8);
        outer[64 + 4*w + 3] = (uint8_t)(ist[w]);
    }
    uint32_t ost[8];
    sha2_32_digest(outer, 64 + inner_bytes, ost, iv);
    for (size_t w = 0; w < out_words; ++w) {
        out[4*w + 0] = (uint8_t)(ost[w] >> 24);
        out[4*w + 1] = (uint8_t)(ost[w] >> 16);
        out[4*w + 2] = (uint8_t)(ost[w] >> 8);
        out[4*w + 3] = (uint8_t)(ost[w]);
    }
}

static void hmac_fam64_scalar(const uint8_t *key, size_t key_len,
                              const uint8_t *msg, size_t msg_len,
                              uint8_t *out, size_t inner_bytes, size_t out_words,
                              const uint64_t iv[8])
{
    uint8_t k[128];
    memset(k, 0, 128);
    memcpy(k, key, key_len);
    uint8_t inner[128 + 2048];
    for (int i = 0; i < 128; ++i) inner[i] = k[i] ^ 0x36;
    memcpy(inner + 128, msg, msg_len);
    uint64_t ist[8];
    sha2_64_digest(inner, 128 + msg_len, ist, iv);
    uint8_t outer[128 + 64];
    for (int i = 0; i < 128; ++i) outer[i] = k[i] ^ 0x5c;
    for (size_t w = 0; w < inner_bytes / 8; ++w)
        for (int b = 0; b < 8; ++b)
            outer[128 + 8*w + b] = (uint8_t)(ist[w] >> (56 - 8*b));
    uint64_t ost[8];
    sha2_64_digest(outer, 128 + inner_bytes, ost, iv);
    for (size_t w = 0; w < out_words; ++w)
        for (int b = 0; b < 8; ++b)
            out[8*w + b] = (uint8_t)(ost[w] >> (56 - 8*b));
}

/* ---- hex decode for the embedded known-answer vectors ---- */
static int hexval(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
static void unhex(const char *h, uint8_t *out, size_t n)
{
    for (size_t i = 0; i < n; ++i)
        out[i] = (uint8_t)((hexval(h[2*i]) << 4) | hexval(h[2*i + 1]));
}

/* RFC 2202 TC1 / RFC 4231 TC1: key = 0x0b x20, data = "Hi There" */
static const char *KAT1_SHA1   = "b617318655057264e28bc0b6fb378c8ef146be00";
static const char *KAT1_SHA224 = "896fb1128abbdf196832107cd49df33f47b4b1169912ba4f53684b22";
static const char *KAT1_SHA256 = "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7";
static const char *KAT1_SHA384 = "afd03944d84895626b0825f4ab46907f15f9dadbe4101ec682aa034c7cebc59cfaea9ea9076ede7f4af152e8b2fa9cb6";
static const char *KAT1_SHA512 = "87aa7cdea5ef619d4ff0b4241a1d6cb02379f4e2ce4ec2787ad0b30545e17cdedaa833b7d6b8a702038b274eaea3f4e4be9d914eeb61f1702e696c203a126854";
/* RFC 2202 TC2: key = "Jefe", data = "what do ya want for nothing?" */
static const char *KAT2_SHA1   = "effcdf6ae5eb2fa2d27416d5f184df9c259a7c79";

/* per-family sweep: in-bound lengths span 0/1, block straddlers, the test
 * knob caps (1900/1830) and the EXACT assembly max (1975/1903) */
static const size_t LEN32[] = {0, 1, 55, 64, 555, 1024, 1900, 1975};
static const size_t KLEN32[] = {20, 0, 64, 7, 32, 16, 48, 3};
static const size_t LEN64[] = {0, 1, 111, 128, 555, 1024, 1830, 1903};
static const size_t KLEN64[] = {32, 0, 128, 7, 64, 16, 96, 3};
#define NLEN ((int)(sizeof(LEN32) / sizeof(LEN32[0])))

/* guard-probe msg_len values: just-over, far, and the WRAP probes */
static const size_t OVER32[] = {1976, 2048, 65536, (size_t)-1, (size_t)-64,
                                (size_t)-63, SIZE_MAX / 2};
static const size_t OVER64[] = {1904, 2048, 65536, (size_t)-1, (size_t)-64,
                                (size_t)-63, SIZE_MAX / 2};
static const size_t KOVER32[] = {65, 1000};
static const size_t KOVER64[] = {129, 1000};

/* ---- shared per-section driver state ---- */
static uint8_t g_keys[SVE_SHA_STREAMS_MAX_32][128];
static uint8_t g_msgs[SVE_SHA_STREAMS_MAX_32][2048];
static const uint8_t *g_kp[SVE_SHA_STREAMS_MAX_32];
static const uint8_t *g_mp[SVE_SHA_STREAMS_MAX_32];

static void fill_all(int n, size_t klen, size_t mlen)
{
    for (int s = 0; s < n; ++s) {
        for (size_t i = 0; i < klen; ++i)
            g_keys[s][i] = byte_at(s, i, 1);
        for (size_t i = 0; i < mlen; ++i)
            g_msgs[s][i] = byte_at(s, i, 0);
        g_kp[s] = g_keys[s];
        g_mp[s] = g_msgs[s];
    }
}

/* one 32-bit-family section: sweep + per-stream oracle compare */
static unsigned section32(const char *name, int which)
{
    const int n = (int)svcntw();
    unsigned fails0 = g_fails;
    uint8_t out20[SVE_SHA_STREAMS_MAX_32][20];
    uint8_t out28[SVE_SHA_STREAMS_MAX_32][28];
    uint8_t out32[SVE_SHA_STREAMS_MAX_32][32];
    for (int li = 0; li < NLEN; ++li) {
        size_t mlen = LEN32[li], klen = KLEN32[li];
        fill_all(n, klen, mlen);
        int rc;
        const uint8_t *obase;
        size_t dlen;
        if (which == 0) {
            rc = hmac_sha1_x8(out20, g_kp, klen, g_mp, mlen);
            obase = out20[0]; dlen = 20;
        } else if (which == 1) {
            rc = hmac_sha224_x8(out28, g_kp, klen, g_mp, mlen);
            obase = out28[0]; dlen = 28;
        } else {
            rc = hmac_sha256_x8(out32, g_kp, klen, g_mp, mlen);
            obase = out32[0]; dlen = 32;
        }
        check(rc == 0, "valid call returned non-zero");
        if (rc != 0)
            continue;
        for (int s = 0; s < n; ++s) {
            uint8_t exp[64];
            if (which == 0)
                hmac_sha1_scalar(g_keys[s], klen, g_msgs[s], mlen, exp);
            else if (which == 1)
                hmac_fam32_scalar(g_keys[s], klen, g_msgs[s], mlen, exp, 28, 7, sha224_iv);
            else
                hmac_fam32_scalar(g_keys[s], klen, g_msgs[s], mlen, exp, 32, 8, sha256_iv);
            if (memcmp(obase + (size_t)s * dlen, exp, dlen) != 0) {
                char what[128];
                snprintf(what, sizeof(what), "%s stream=%d len=%zu", name, s, mlen);
                check(0, what);
            }
            fnv_bits(obase + (size_t)s * dlen, dlen);
        }
    }
    printf("mode=%s streams=%d lengths=%d FAILS=%u\n", name, n, NLEN,
           g_fails - fails0);
    return g_fails - fails0;
}

/* one 64-bit-family section */
static unsigned section64(const char *name, int which)
{
    const int n = (int)svcntd();
    unsigned fails0 = g_fails;
    uint8_t out48[SVE_SHA_STREAMS_MAX_64][48];
    uint8_t out64[SVE_SHA_STREAMS_MAX_64][64];
    for (int li = 0; li < NLEN; ++li) {
        size_t mlen = LEN64[li], klen = KLEN64[li];
        fill_all(n, klen, mlen);
        int rc;
        const uint8_t *obase;
        size_t dlen;
        if (which == 0) {
            rc = hmac_sha384_x4(out48, g_kp, klen, g_mp, mlen);
            obase = out48[0]; dlen = 48;
        } else {
            rc = hmac_sha512_x4(out64, g_kp, klen, g_mp, mlen);
            obase = out64[0]; dlen = 64;
        }
        check(rc == 0, "valid call returned non-zero");
        if (rc != 0)
            continue;
        for (int s = 0; s < n; ++s) {
            uint8_t exp[64];
            if (which == 0)
                hmac_fam64_scalar(g_keys[s], klen, g_msgs[s], mlen, exp, 48, 6, sha384_iv);
            else
                hmac_fam64_scalar(g_keys[s], klen, g_msgs[s], mlen, exp, 64, 8, sha512_iv);
            if (memcmp(obase + (size_t)s * dlen, exp, dlen) != 0) {
                char what[128];
                snprintf(what, sizeof(what), "%s stream=%d len=%zu", name, s, mlen);
                check(0, what);
            }
            fnv_bits(obase + (size_t)s * dlen, dlen);
        }
    }
    printf("mode=%s streams=%d lengths=%d FAILS=%u\n", name, n, NLEN,
           g_fails - fails0);
    return g_fails - fails0;
}

/* known-answer section: every stream carries the SAME key/message; all
 * streams must reproduce the published digest. Also self-checks the scalar
 * oracle against the same vector (oracle==published, SVE==published). */
static void kat_one(const char *name, const uint8_t *key, size_t klen,
                    const uint8_t *msg, size_t mlen, const char *hex,
                    int family /* 0 sha1, 1 sha224, 2 sha256, 3 sha384, 4 sha512 */)
{
    size_t dlen = strlen(hex) / 2;
    uint8_t exp[64];
    unhex(hex, exp, dlen);
    uint8_t oexp[64];
    if (family == 0)      hmac_sha1_scalar(key, klen, msg, mlen, oexp);
    else if (family == 1) hmac_fam32_scalar(key, klen, msg, mlen, oexp, 28, 7, sha224_iv);
    else if (family == 2) hmac_fam32_scalar(key, klen, msg, mlen, oexp, 32, 8, sha256_iv);
    else if (family == 3) hmac_fam64_scalar(key, klen, msg, mlen, oexp, 48, 6, sha384_iv);
    else                  hmac_fam64_scalar(key, klen, msg, mlen, oexp, 64, 8, sha512_iv);
    check(memcmp(oexp, exp, dlen) == 0, "scalar oracle disagrees with RFC vector");

    if (family <= 2) {
        const int n = (int)svcntw();
        uint8_t out20[SVE_SHA_STREAMS_MAX_32][20];
        uint8_t out28[SVE_SHA_STREAMS_MAX_32][28];
        uint8_t out32[SVE_SHA_STREAMS_MAX_32][32];
        for (int s = 0; s < n; ++s) { g_kp[s] = key; g_mp[s] = msg; }
        int rc;
        const uint8_t *obase;
        if (family == 0)      { rc = hmac_sha1_x8(out20, g_kp, klen, g_mp, mlen); obase = out20[0]; }
        else if (family == 1) { rc = hmac_sha224_x8(out28, g_kp, klen, g_mp, mlen); obase = out28[0]; }
        else                  { rc = hmac_sha256_x8(out32, g_kp, klen, g_mp, mlen); obase = out32[0]; }
        check(rc == 0, "KAT call returned non-zero");
        for (int s = 0; s < n; ++s)
            if (memcmp(obase + (size_t)s * dlen, exp, dlen) != 0) {
                char what[96];
                snprintf(what, sizeof(what), "KAT %s stream=%d", name, s);
                check(0, what);
            }
    } else {
        const int n = (int)svcntd();
        uint8_t out48[SVE_SHA_STREAMS_MAX_64][48];
        uint8_t out64[SVE_SHA_STREAMS_MAX_64][64];
        for (int s = 0; s < n; ++s) { g_kp[s] = key; g_mp[s] = msg; }
        int rc;
        const uint8_t *obase;
        if (family == 3) { rc = hmac_sha384_x4(out48, g_kp, klen, g_mp, mlen); obase = out48[0]; }
        else             { rc = hmac_sha512_x4(out64, g_kp, klen, g_mp, mlen); obase = out64[0]; }
        check(rc == 0, "KAT call returned non-zero");
        for (int s = 0; s < n; ++s)
            if (memcmp(obase + (size_t)s * dlen, exp, dlen) != 0) {
                char what[96];
                snprintf(what, sizeof(what), "KAT %s stream=%d", name, s);
                check(0, what);
            }
    }
}

/* guard probes: every over-bound msg_len / key_len MUST return -1 */
static void guard_probes(void)
{
    uint8_t out20[SVE_SHA_STREAMS_MAX_32][20];
    uint8_t out28[SVE_SHA_STREAMS_MAX_32][28];
    uint8_t out32[SVE_SHA_STREAMS_MAX_32][32];
    uint8_t out48[SVE_SHA_STREAMS_MAX_64][48];
    uint8_t out64[SVE_SHA_STREAMS_MAX_64][64];
    const int nw = (int)svcntw(), nd = (int)svcntd();
    fill_all(nw > nd ? nw : nd, 20, 64);
    unsigned g0 = g_fails;

    for (int i = 0; i < (int)(sizeof(OVER32) / sizeof(OVER32[0])); ++i) {
        size_t ml = OVER32[i];
        check(hmac_sha1_x8(out20, g_kp, 20, g_mp, ml) == -1, "sha1 msg guard");
        check(hmac_sha224_x8(out28, g_kp, 20, g_mp, ml) == -1, "sha224 msg guard");
        check(hmac_sha256_x8(out32, g_kp, 20, g_mp, ml) == -1, "sha256 msg guard");
    }
    for (int i = 0; i < (int)(sizeof(OVER64) / sizeof(OVER64[0])); ++i) {
        size_t ml = OVER64[i];
        check(hmac_sha384_x4(out48, g_kp, 20, g_mp, ml) == -1, "sha384 msg guard");
        check(hmac_sha512_x4(out64, g_kp, 20, g_mp, ml) == -1, "sha512 msg guard");
    }
    for (int i = 0; i < (int)(sizeof(KOVER32) / sizeof(KOVER32[0])); ++i) {
        size_t kl = KOVER32[i];
        check(hmac_sha1_x8(out20, g_kp, kl, g_mp, 64) == -1, "sha1 key guard");
        check(hmac_sha224_x8(out28, g_kp, kl, g_mp, 64) == -1, "sha224 key guard");
        check(hmac_sha256_x8(out32, g_kp, kl, g_mp, 64) == -1, "sha256 key guard");
    }
    for (int i = 0; i < (int)(sizeof(KOVER64) / sizeof(KOVER64[0])); ++i) {
        size_t kl = KOVER64[i];
        check(hmac_sha384_x4(out48, g_kp, kl, g_mp, 64) == -1, "sha384 key guard");
        check(hmac_sha512_x4(out64, g_kp, kl, g_mp, 64) == -1, "sha512 key guard");
    }
    printf("guard-probes msg=%zu+%zu key=%zu+%zu FAILS=%u\n",
           sizeof(OVER32) / sizeof(OVER32[0]) * 3,
           sizeof(OVER64) / sizeof(OVER64[0]) * 2,
           sizeof(KOVER32) / sizeof(KOVER32[0]) * 3,
           sizeof(KOVER64) / sizeof(KOVER64[0]) * 2,
           g_fails - g0);
}

int main(int argc, char **argv)
{
    const char *mode = argc > 1 ? argv[1] : "fixed";
    unsigned seed = argc > 2 ? (unsigned)atoi(argv[2]) : 1;
    g_random = strcmp(mode, "random") == 0;
    if (g_random)
        xs_state = seed ? seed : 1;

    /* VL gate (mirror verify.cpp) + the 17 tests' init-side glue invariant */
    const int nw = (int)svcntw(), nd = (int)svcntd();
    const unsigned long vb = (unsigned long)svcntb();
    if (nw < 4 || nw > SVE_SHA_STREAMS_MAX_32 ||
        nd < 2 || nd > SVE_SHA_STREAMS_MAX_64) {
        printf("unsupported VL (svcntw=%d svcntd=%d; arrays sized for "
               "128..1024-bit)\n", nw, nd);
        return 3;
    }
    if ((long)vb / 4 != nw || (long)vb / 8 != nd) {
        printf("lanes invariant broken: svl=%lu svcntw=%d svcntd=%d\n",
               vb, nw, nd);
        return 1;
    }
    printf("vl_bytes=%lu svcntw=%d svcntd=%d lanes_invariant=ok mode=%s seed=%u\n",
           vb, nw, nd, mode, seed);

    /* RFC known-answer anchors (published vectors; hex verified with an
     * independent python3 hmac on 2026-10-25) */
    static const uint8_t k1[20] = {0x0b,0x0b,0x0b,0x0b,0x0b,0x0b,0x0b,0x0b,
                                   0x0b,0x0b,0x0b,0x0b,0x0b,0x0b,0x0b,0x0b,
                                   0x0b,0x0b,0x0b,0x0b};
    static const uint8_t d1[8] = {'H','i',' ','T','h','e','r','e'};
    static const uint8_t k2[4] = {'J','e','f','e'};
    static const char d2[] = "what do ya want for nothing?";
    unsigned k0 = g_fails;
    kat_one("rfc2202-tc1-sha1", k1, 20, d1, 8, KAT1_SHA1, 0);
    kat_one("rfc4231-tc1-sha224", k1, 20, d1, 8, KAT1_SHA224, 1);
    kat_one("rfc4231-tc1-sha256", k1, 20, d1, 8, KAT1_SHA256, 2);
    kat_one("rfc4231-tc1-sha384", k1, 20, d1, 8, KAT1_SHA384, 3);
    kat_one("rfc4231-tc1-sha512", k1, 20, d1, 8, KAT1_SHA512, 4);
    kat_one("rfc2202-tc2-sha1", k2, 4, (const uint8_t *)d2, strlen(d2), KAT2_SHA1, 0);
    printf("kat-vectors=6 FAILS=%u\n", g_fails - k0);

    /* per-stream sweep sections */
    section32("hmac_sha1", 0);
    section32("hmac_sha224", 1);
    section32("hmac_sha256", 2);
    section64("hmac_sha384", 0);
    section64("hmac_sha512", 1);

    /* capacity-guard probes (incl. the size_t wrap probes) */
    guard_probes();

    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    printf("CHECKSUM=%016llx\n", (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
