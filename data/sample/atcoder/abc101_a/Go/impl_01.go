package main

import "fmt"

func main() {
	var s string
	var n int = 0
	fmt.Scanf("%s", &s)
	for _, v := range s {
		if v == '+' {
			n++
		} else {
			n--
		}
	}
	fmt.Println(n)
}
