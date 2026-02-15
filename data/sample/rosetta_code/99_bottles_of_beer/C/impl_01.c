#include <stdio.h>
main(){_=100;while(--_)printf("%i bottle%s of beer in the wall,\n%i bottle%"
"s of beer.\nTake one down, pass it round,\n%s%s\n\n",_,_-1?"s":"",_,_-1?"s"
:"",_-1?(char[]){(_-1)/10?(_-1)/10+48:(_-1)%10+48,(_-1)/10?(_-1)%10+48:2+30,
(_-1)/10?32:0,0}:"",_-1?"bottles of beer in the wall":"No more beers");}

/*
 * 99 Bottles, C, KISS (i.e. keep it simple and straightforward) version
 */

#include <stdio.h>

int main(void)
{
  int n;

  for( n = 99; n > 2; n-- )
    printf(
      "%d bottles of beer on the wall, %d bottles of beer.\n"
      "Take one down and pass it around, %d bottles of beer on the wall.\n\n", 
       n, n, n - 1);

  printf(  
      "2 bottles of beer on the wall, 2 bottles of beer.\n"
      "Take one down and pass it around, 1 bottle of beer on the wall.\n\n"                  

      "1 bottle of beer on the wall, 1 bottle of beer.\n"
      "Take one down and pass it around, no more bottles of beer on the wall.\n\n"                  

      "No more bottles of beer on the wall, no more bottles of beer.\n" 
      "Go to the store and buy some more, 99 bottles of beer on the wall.\n");

      return 0;
}