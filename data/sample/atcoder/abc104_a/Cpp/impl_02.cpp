#include <bits/stdc++.h>
using namespace std;

#define int long long 
#define double long double
signed main() 
{
    int R;
    cin >> R;
    if(R < 1200){
          cout << "ABC";
          return 0;
    }
    else if(R < 2800){
      cout << "ARC";
      return 0;
    }
    cout << "AGC";
    return 0;
}