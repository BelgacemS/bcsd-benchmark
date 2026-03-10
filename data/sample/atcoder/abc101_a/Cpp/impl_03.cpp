#include <bits/stdc++.h>
using namespace std;
#define ll long long
ll sum;
int main(){
    for(ll i = 1;i <= 4;i++){
        char c;
        cin >> c;
        if(c == '-'){
            sum--;
        }else{
            sum++;
        }
    }
    cout << sum << "\n";
}