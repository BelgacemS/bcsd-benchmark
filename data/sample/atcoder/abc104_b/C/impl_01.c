#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

int main(void){
  // int a, b;
  // scanf("%d %d", &a, &b);
  char s[11];
  scanf("%s", s);
  int flag = 1;
  if(s[0] == 'A'){
    int cntC = 0;
    for(int i = 2; i < strlen(s) - 1; i++){
      // printf("%c ", s[i]);
      if(s[i] == 'C'){
        cntC++;
      }
    }
    if(cntC == 1){
      for(int i = 0; i < strlen(s); i++){
        if(s[i] != 'A' && s[i] != 'C'){
          if('a' <= s[i] && s[i] <= 'z'){
            continue;
          }else{
            // printf("a\n");
            flag = 0;
            break;
          }
        }
      }
    }else{
      // printf("c\n");
      flag = 0;
    }
  }else{
    // printf("d\n");
    flag = 0;
  }
  if(flag){
    printf("AC\n");
  }else{
    printf("WA\n");
  }
  return 0;
}