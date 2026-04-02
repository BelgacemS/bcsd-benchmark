#include <iostream>
#include <unordered_map>
#include <algorithm>
using namespace std;


int main() {


	string s1, s2;
	cin >> s1;
	cin >> s2;

	s1 = s1 + s1;
	if (s1.find(s2) == string::npos)
		cout << "No";
	else
		cout << "Yes";
	
	
	return 0;
}

