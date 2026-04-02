package main

import (
	"fmt"
)

func main() {
	var r int
	fmt.Scan(&r)
	if r < 1200 {
		fmt.Println("ABC")
	} else if r < 2800 {
		fmt.Println("ARC")
	} else {
		fmt.Println("AGC")
	}
}
