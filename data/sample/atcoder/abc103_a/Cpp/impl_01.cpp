#include <iostream>
#include <algorithm>
#include <cmath>

using namespace std;

int minimum (int , int , int );
int maximum (int , int , int );

int main ()
{
    int A1 ,A2 ,A3 ;
    cin >> A1 >> A2 >> A3 ;
    cout << abs(min({A1 , A2 , A3}) - max({ A1 , A2 , A3}));
    return 0;
}
