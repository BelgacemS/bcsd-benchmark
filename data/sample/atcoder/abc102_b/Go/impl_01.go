package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	scanner := bufio.NewReader(os.Stdin)
	var n int
	fmt.Fscan(scanner, &n)
	a := make([]int, n)
	max := 0
	min := 1000000000
	for i := 0; i < n; i++ {
		fmt.Fscan(scanner, &a[i])
		if a[i] > max {
			max = a[i]
		}
		if min > a[i] {
			min = a[i]
		}
	}
	fmt.Println(max - min)
}
