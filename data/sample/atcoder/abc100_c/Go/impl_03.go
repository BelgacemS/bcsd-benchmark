package main

import (
	"bufio"
	"fmt"
	"math"
	"os"
	"strconv"
)


func main() {
	n := getI()
	A := getInts(n)

	ans := 0
	for i := 0; i < n; i++ {
		for A[i]%2 == 0 {
			A[i] /= 2
			ans++
		}
	}
	out(ans)
}

var sc = bufio.NewScanner(os.Stdin)

func init() {
	sc.Split(bufio.ScanWords)
	sc.Buffer([]byte{}, math.MaxInt32)
}

func getI() int {
	sc.Scan()
	i, e := strconv.Atoi(sc.Text())
	if e != nil {
		panic(e)
	}
	return i
}

func getInts(N int) []int {
	ret := make([]int, N)
	for i := 0; i < N; i++ {
		ret[i] = getI()
	}
	return ret
}

func getF() float64 {
	sc.Scan()
	i, e := strconv.ParseFloat(sc.Text(), 64)
	if e != nil {
		panic(e)
	}
	return i
}

func out(x ...interface{}) {
	fmt.Println(x...)
}
