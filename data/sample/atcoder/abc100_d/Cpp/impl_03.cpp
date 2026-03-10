#include<iostream>
#include<vector>
#include<cmath>
using namespace std;
int main(){
  int N,M;cin>>N>>M;
  vector<long long> P(N);
  vector<long long> x(N+1),y(N+1),z(N+1);for(int i=1;i<=N;i++)cin>>x[i]>>y[i]>>z[i];
  vector<long long> signx={1,-1};
  vector<long long> signy={1,-1};
  vector<long long> signz={1,-1};
  long long answer=-1e15;
  for(auto sx:signx){
    for(auto sy:signy){
      for(auto sz:signz){
        vector<vector<long long>> dp(N+1,vector<long long>(M+1,-1e15));// dp[i][j]はi番目まででj個使った時の最大．
        dp[0][0]=0;
        for(int i=1;i<=N;i++){
          dp[i]=dp[i-1];
          for(int j=1;j<=M;j++){
            dp[i][j]=max(dp[i-1][j],dp[i-1][j-1]+sx*x[i]+sy*y[i]+sz*z[i] );
          }
        }
        answer=max(answer,dp[N][M]);
      }
    }
  }
  cout <<answer<<endl;
}