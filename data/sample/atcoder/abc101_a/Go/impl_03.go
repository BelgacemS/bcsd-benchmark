package main

import (
	"fmt"
)
 
func main() {
	var s string
	var i int
	fmt.Scanf("%s", &s)
	for _, c := range s {
		if (c == '+') {
		  i++
		}
		if (c == '-') {
		  i--
		}
	}
	fmt.Printf("%d", i)
}