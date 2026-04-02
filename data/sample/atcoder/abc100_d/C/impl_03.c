#include<stdio.h>
#include<stdlib.h>

int down(const void *a,const void *b){
  if(*(long long *)a > *(long long *)b){
    return -1;
  }
  else if(*(long long *)a < *(long long *)b){
    return 1;
  }
  else if(*(long long *)a == *(long long *)b){
    return 0;
  }
}

int main(void){
  int n , m;
  scanf("%d %d",&n ,&m);

  long long x[n] , y[n] , z[n];
  for(int i = 0;i < n;i ++){
    scanf("%lld %lld %lld",&x[i] ,&y[i] ,&z[i]);
  }

  long long cake1[n] , cake2[n] , cake3[n] , cake4[n];
  long long cake5[n] , cake6[n] , cake7[n] , cake8[n];

  for(int i = 0;i < n;i ++){
    cake1[i] = x[i] + y[i] + z[i];
    cake2[i] = x[i] + y[i] - z[i];
    cake3[i] = x[i] - y[i] + z[i];
    cake4[i] = x[i] - y[i] - z[i];
    cake5[i] = -x[i] + y[i] + z[i];
    cake6[i] = -x[i] + y[i] - z[i];
    cake7[i] = -x[i] - y[i] + z[i];
    cake8[i] = -x[i] - y[i] - z[i];
  }

  qsort(cake1,n,sizeof(long long),down);
  qsort(cake2,n,sizeof(long long),down);
  qsort(cake3,n,sizeof(long long),down);
  qsort(cake4,n,sizeof(long long),down);
  qsort(cake5,n,sizeof(long long),down);
  qsort(cake6,n,sizeof(long long),down);
  qsort(cake7,n,sizeof(long long),down);
  qsort(cake8,n,sizeof(long long),down);

  long long ans = 0;
  long long count[8] = {0};
  for(int i = 0;i < m;i ++){
    ans += cake1[i];
    count[0] += cake2[i];
    count[1] += cake3[i];
    count[2] += cake4[i];
    count[3] += cake5[i];
    count[4] += cake6[i];
    count[5] += cake7[i];
    count[6] += cake8[i];
  }

  for(int i = 0;i <= 6;i ++){
    if(ans < count[i]){
      ans = count[i];
    }
  }

  printf("%lld\n",ans);

  return 0;
}