package main

import (
	"fmt"
)

func main() {
	var s, t string
	fmt.Scan(&s)
	fmt.Scan(&t)

	if s == t {
		fmt.Println("Yes")
		return
	}

	ok := false
	n := len(s)
	for i := 1; i < n; i++ {
		s = s[n-1:] + s[0:n-1]
		if s == t {
			ok = true
			break
		}

	}

	if ok {
		fmt.Println("Yes")
	} else {
		fmt.Println("No")
	}
}
