package main

import (
	"fmt"
	"sort"
)

func abs(a int) int {
	if a < 0 {
		return -a
	}
	return a
}

func main() {
	var a = make([]int, 3)
	fmt.Scan(&a[0], &a[1], &a[2])
	sort.Ints(a)
	fmt.Println(abs(a[1]-a[0]) + abs(a[2]-a[1]))

}