#include<bits/stdc++.h>
using namespace std;
int n,m;
int a[100010],s[100010];
map<int,int> mp;
long long ans;
int main(){
	ios::sync_with_stdio(false);
	cin.tie(0),cout.tie(0);
	cin>>n>>m;
	for(int i=1;i<=n;i++){
		cin>>a[i];
		s[i]=s[i-1]+a[i];
		s[i]%=m;
	}
	mp[0]=1;
	for(int i=1;i<=n;i++){
		ans+=mp[s[i]];
		mp[s[i]]++;
	}
	cout<<ans;
	return 0;
}