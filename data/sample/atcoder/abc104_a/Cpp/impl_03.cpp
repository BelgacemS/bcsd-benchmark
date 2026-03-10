#include <iostream>
using namespace std;
int main() {
  long long n;
  cin >> n;
  if (n < 1200) {
    cout << "ABC\n";
  } else if (n < 2800) {
    cout << "ARC\n";
  } else if (n >= 2800){
    cout << "AGC\n";
  }
  return 0;
}