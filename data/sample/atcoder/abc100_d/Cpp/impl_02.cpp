#include <iostream>
#include <queue>
using namespace std;
int N,M;
long X[1000],Y[1000],Z[1000];
int main(){
    cin >> N >> M;
    for(int i = 0; i < N; i++) cin >> X[i] >> Y[i] >> Z[i];

    long ans = 0;
    for(int b = 0; b < 8; b++){
        long sgn[3];
        for(int d = 0; d < 3; d++){
            if((b>>d)&1) sgn[d] = 1;
            else sgn[d] = -1;
        }
        priority_queue<tuple<long,long,long,long>> P;
        for(int i = 0; i < N; i++){
            long x = X[i] * sgn[0];
            long y = Y[i] * sgn[1];
            long z = Z[i] * sgn[2];
            P.emplace(x+y+z,x,y,z);
        }
        long Xsum = 0, Ysum = 0, Zsum = 0;
        for(int i = 0; i < M; i++){
            auto [s,x,y,z] = P.top(); P.pop();
            Xsum += x;
            Ysum += y;
            Zsum += z;
        }
        ans = max(ans, Xsum + Ysum + Zsum);
    }
    cout << ans << endl;
}