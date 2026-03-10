package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
)

func main() {
	N := getI()

	if N % 2 == 0 {
		out(N)
	} else {
		out(2 * N)
	}
}

var sc = bufio.NewScanner(os.Stdin)

func getI() int {
	sc.Scan()
	i, e := strconv.Atoi(sc.Text())
	if e != nil {
		panic(e)
	}
	return i
}


func out(x ...interface{}) {
	fmt.Println(x...)
}
