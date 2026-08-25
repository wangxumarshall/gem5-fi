#include <unistd.h>
int main(void){
    const char msg[] = "Hello, AArch64 CHAOS!\n";
    write(1, msg, sizeof(msg)-1);
    return 0;
}
