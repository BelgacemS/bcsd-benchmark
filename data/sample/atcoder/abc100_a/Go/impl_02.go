package main

import (
	"fmt"
)

func main() {
	var a int
	var b int
	fmt.Scan(&a, &b)
	//となりあわない
	if a <= 8 && b <= 8 {

		fmt.Print("Yay!")
	} else {
		fmt.Print(":(")
	}
}
