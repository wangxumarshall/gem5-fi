/* ptr_chase_kernel — §2.1/§2.4 D: linked-list pointer chase.
 * 遍历链表让指针寄存器(x10)长存活——复现 method2 的 find_busiest_group。
 * Build: gcc -static -O2 -o ptr_chase_kernel ptr_chase_kernel.c
 */
#include <stdio.h>
#include <stdint.h>
struct Node { struct Node *next; uint64_t val; };
static uint64_t cs = 0xcbf29ce484222325ULL;
int main(void) {
    struct Node nodes[256];
    for (int i = 0; i < 256; i++) { nodes[i].next = &nodes[(i*7+1)%256]; nodes[i].val = i*13; }
    struct Node *p = &nodes[0];
    uint64_t sum = 0;
    for (int i = 0; i < 256; i++) { sum ^= p->val; p = p->next; }
    cs ^= sum; cs *= 0x100000001b3ULL;
    printf("%016llx\n", cs);
    return 0;
}
