package main

import (
	"fmt"
	"math"
)

func main() {

	var d int
	var n int
	var ans int
	fmt.Scan(&d, &n) // d

	for i := 1; i <= n; i++ {
		ans = i * int(math.Pow(100, float64(d)))
	}

	// d 0  d 1
	if n == 100 && d == 0 { //101  1100
		fmt.Print(ans + 1)
	} else if n == 100 && d == 1 {
		fmt.Print(ans + 100)
	} else if n == 100 && d == 2 {
		fmt.Print(ans + 10000)
	} else {
		fmt.Print(ans)
	}

	//100で一回　100 200 300....
	//100で二回  10000 20000 30000

	//100 でちょうどD回割りきれる
	//n番目に小さいもの

}
