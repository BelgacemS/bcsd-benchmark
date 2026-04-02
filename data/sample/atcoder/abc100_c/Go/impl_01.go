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
	for i := 0; i < n; i++ {
		fmt.Fscan(scanner, &a[i])
	}
	ans := 0
	for _, v := range a {
		for {
			if v%2 == 0 {
				ans++
				v = v / 2
			} else {
				break
			}
		}
	}
	fmt.Println(ans)
}
