#include <bits/stdc++.h>
using namespace std;

int ctTwo(int n) {
    int ct = 0;
    while(n%2 == 0) {
        ct += 1;
        n = n/2;
    }
    return ct;
}

int main() {

    long long n;
    cin>>n;
    vector<long long> a(n,0);
    for(int i=0;i<n;i++) cin>>a[i];
    
    int sm = 0;
    for(int i:a) {
        sm += ctTwo(i);
    }
    cout<<sm<<endl;
 
}