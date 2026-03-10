package main

import (
	"fmt"
)

func main() {
	var N, K int
	fmt.Scanf("%d %d", &N, &K)
	
	if N % K == 0 {
		fmt.Println(0)
	} else {
		fmt.Println(1)
	}
}
