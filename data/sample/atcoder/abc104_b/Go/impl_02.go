package main

import (
	"fmt"
	"strings"
	"unicode"
)

const AC = "AC"
const WA = "WA"

func CountUppercase(s string) int {
	count := 0
	for _, r := range s {
		if unicode.IsUpper(r) {
			count++
		}
	}
	return count
}

func main() {
	var s string
	fmt.Scan(&s)

	runes := []rune(s)
	if runes[0] != 'A' {
		fmt.Println(WA)
		return
	}
	cCount := strings.Count(string(runes[2:len(runes)-1]), "C")
	if cCount != 1 {
		fmt.Println(WA)
		return
	}

	if CountUppercase(s) > 2 {
		fmt.Println(WA)
		return
	}

	fmt.Println(AC)
}
