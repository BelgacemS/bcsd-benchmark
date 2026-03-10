package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

func main() {
	var (
		N      int
		answer int = 0
	)

	sc := bufio.NewScanner(os.Stdin)

	buf := make([]byte, bufio.MaxScanTokenSize)
	sc.Buffer(buf, 8*1024*1024)

	sc.Scan()
	N, _ = strconv.Atoi(sc.Text())

	sc.Scan()
	inputs := strings.Split(sc.Text(), " ")

	for i := 0; i < N; i++ {
		temp, _ := strconv.Atoi(inputs[i])
		answer += temp
	}

	fmt.Println(answer - N)
}
