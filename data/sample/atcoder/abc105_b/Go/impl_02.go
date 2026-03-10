package main

import (
	"fmt"
)

func main() {
	var N int
	fmt.Scanf("%d", &N)

	// 4x + 7y = N となるパターンを探す
	for x := 0; x <= N / 4; x++ {
		for y := 0; y <= N / 7; y++ {
			if 4*x + 7*y == N {
				fmt.Println("Yes")
				return
			}
		}
	}

	fmt.Println("No")
}
