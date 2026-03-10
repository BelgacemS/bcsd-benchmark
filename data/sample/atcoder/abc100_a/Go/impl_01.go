package main

import (
	"fmt"
)

// あー桁くりあがりが考慮されてないか。
func main() {
	var a, b int
	fmt.Scan(&a, &b)

	if a > 8 || b > 8 {
		fmt.Println(":(")
	} else {
		fmt.Println("Yay!")
	}
}
