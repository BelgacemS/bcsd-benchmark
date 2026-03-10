package main

import (
	"fmt"
	"math"
)

func main() {
	var d, n int
	fmt.Scan(&d, &n)
	t := int(math.Pow(100, float64(d)))
	ans := n * t
	if n == 100 {
		ans += t
	}
	fmt.Println(ans)
}
