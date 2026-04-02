// https://atcoder.jp/contests/abc105/tasks/abc105_b
package main

import "fmt"

func main() {
	n:=0
	fmt.Scan(&n)
	a:="No"
	for i:=0; i<=n/4; i++ {
		if (n-i*4)%7==0 {
			a="Yes"
			break
		}
	}
	fmt.Println(a)
}
