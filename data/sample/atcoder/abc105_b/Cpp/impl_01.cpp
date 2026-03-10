#include <iostream>
using namespace std;
int main() {
  int n;
  cin >> n;
  for (int i = 0; i <= n; i += 7) {
    if ((n - i) % 4 == 0) {
      cout << "Yes\n";
      return 0;
    }
  }
  cout << "No\n";
  return 0;
}