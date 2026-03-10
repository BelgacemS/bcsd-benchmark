#include <stdio.h>
unsigned const N = 100000;
unsigned const MOD = 1000000000+7;

int main() {
  char S[N+8];
  fgets(S, sizeof(S), stdin);

  unsigned pow3[N+8];
  pow3[-1+1] = 0;
  pow3[ 0+1] = 1;
  unsigned long long a=0, qL=0, qR=0, c=0;
  for (int i=0; S[i]!='\n'; ++i) {
    pow3[i+1+1] = (pow3[i+1] * 3) % MOD;
    if (S[i] == 'C')
      ++c;
    if (S[i] == '?')
      ++qR;
  }

  unsigned long long ans=0;
  for (int i=0; S[i]!='\n'; ++i) {
    if (S[i] == 'A')
      ++a;
    if (S[i] == 'B' || S[i] == '?') {
      if (S[i] == '?')
        --qR;
      ans += (a  * pow3[qL  +1] % MOD) * (c  * pow3[qR  +1] % MOD);
      ans += (a  * pow3[qL  +1] % MOD) * (qR * pow3[qR-1+1] % MOD);
      ans += (qL * pow3[qL-1+1] % MOD) * (c  * pow3[qR  +1] % MOD);
      ans += (qL * pow3[qL-1+1] % MOD) * (qR * pow3[qR-1+1] % MOD);
      ans %= MOD;
      if (S[i] == '?')
        ++qL;
    }
    if (S[i] == 'C')
      --c;
  }

  printf("%llu\n", ans);
  return 0;
}