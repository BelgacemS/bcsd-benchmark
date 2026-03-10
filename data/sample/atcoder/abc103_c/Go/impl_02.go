package main

import (
	"fmt"
)

func main() {
	var N int
	fmt.Scanf("%d", &N)
	A := make([]int, N)
	for i := 0; i < N; i++ {
		fmt.Scanf("%d", &A[i])
	}

	var sum int
	for _, a := range A {
		sum += a - 1
	}

	fmt.Println(sum)
}
