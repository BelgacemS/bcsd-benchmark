package main

import (
	"fmt"
	"unicode"
)

func main() {
	var S string
	fmt.Scanf("%s", &S)

	if S[0] != 'A' {
		fmt.Println("WA")
		return
	}

	// 前から3文字、後ろから2文字の閉区間に 'C' が1文字だけあるべき
	p := S[2:len(S)-1]
	cnt := 0
	for _, c := range p {
		if c == 'C' {
			cnt++
		}
	}
	if cnt != 1 {
		fmt.Println("WA")
		return
	}

	// 大文字数を数える。上記条件の2つ以外は全て小文字 => cnt = 2 であるべき
	cnt = 0
	for _, c := range S {
		if !unicode.IsLower(c) {
			cnt++
		}
	}
	if cnt != 2 {
		fmt.Println("WA")
		return
	}


	fmt.Println("AC")
}
