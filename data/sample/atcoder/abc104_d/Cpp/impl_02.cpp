#include<bits/stdc++.h>
using namespace std;
const long long mod=1e9+7;
int main(){
  string S;cin>>S;
  vector<vector<long long>> dp(S.size()+1,vector<long long>(4,0));
  dp[0][0]=1;
  string X="ABC";
 
  for(int i=1;i<=S.size();i++){
    if('?'==S.at(i-1)){
      for(int j=0;j<=3;j++)dp[i][j]=3*dp[i-1][j];
      for(int j=0;j<3;j++)dp[i][j+1]+=dp[i-1][j];
    }else{
      dp[i]=dp[i-1];
      for(auto itr=X.begin();itr!=X.end();itr++){
      
        if(*itr==S.at(i-1)){
          dp[i][distance(X.begin(),itr)+1]+=dp[i-1][distance(X.begin(),itr)];
        } 
      }
      
      
    }
    
    
    
    
    for(int j=0;j<=3;j++)dp[i][j]%=mod;
    //for(int j=1;j<=3;j++)cout <<dp[i][j]<<' ';
    //cout <<"\n";
    
  }
  cout <<dp[S.size()][3];
}