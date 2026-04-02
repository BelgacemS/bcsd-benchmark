package main

import (
	"bufio"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"
)

func main() {
	N := getI()
	sc.Scan()
	A := make([]int, N)
	for i, a := range strings.Split(sc.Text(), " ") {
		A[i], _ = strconv.Atoi(a)
	}


	sort.Slice(A, func (i, j int) bool {
		return A[i] < A[j]
	})
	diff := A[0] - A[len(A)-1]
	if diff < 0 {
		diff = -diff
	}
	out(diff)
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
