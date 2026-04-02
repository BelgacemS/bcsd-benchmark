#include <stdio.h>
#include <stdlib.h>

struct _war {
  int s;
  int e;
} *war;

int comp(const void *a, const void *b){
  struct _war *aa = (struct _war *)a;
  struct _war *bb = (struct _war *)b;
  if( aa->e < bb->e ){
    return -1;
  }
  if( aa->e > bb->e ){
    return 1;
  }
  return 0;
}

int main(void){
  char buf[128];
  char *p;
  int n,m;
  int i;
  int last;
  int x;

  fgets(buf,sizeof(buf),stdin);
  n = strtol(buf,&p,10);
  m = strtol(p+1,NULL,10);

  war = (struct _war *)malloc(sizeof(struct _war)*m);
  for(i=0;i<m;i++){
    fgets(buf,sizeof(buf),stdin);
    war[i].s = strtol(buf,&p,10);
    war[i].e = strtol(p+1,NULL,10);
  }

  qsort(war, m, sizeof(struct _war), comp);

  last=0;
  x=0;
  for(i=0;i<m;i++){
    if( last <= war[i].s ){
      x++;
      last=war[i].e;
    }
  }
  
  printf("%d\n",x);
}
