package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

func run() {
	S := getS()
	ans := 0
	for _, s := range strings.Split(S, "") {
		if s == "+" {
			ans++
		} else {
			ans--
		}
	}

	fmt.Println(ans)
}

func main() { run() }

var sc = bufio.NewScanner(os.Stdin)

func getS() string {
	sc.Scan()
	return sc.Text()
}
