#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

int main(void){
  char s[102];
  char t[102];
  scanf("%s\n%s", s, t);
  for(int i = 0; i < strlen(s); i++){
    char temp = s[strlen(s)-1];
    for(int j = strlen(s) - 2; j >= 0; j--){
      s[j+1] = s[j];
    }
    s[0] = temp;
    if(strcmp(s, t) == 0){
      printf("Yes\n");
      return 0;
    }
  }
  printf("No\n");
  return 0;
}