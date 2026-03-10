#include <bits/stdc++.h>
using namespace std;

int main()
{
  string s;
  cin>>s;

  int i,n=0;
  for(i=0; i<=s.length();i++){
     if(s[i]=='+'){  
     n++;
     }
     else if(s[i]=='-')
      n--;

  } 
  
  cout<<n<<endl;


}