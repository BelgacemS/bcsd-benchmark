package main

import (
	"bufio"
	"fmt"
	"os"
)

var (
	sc = bufio.NewScanner(os.Stdin)
	wr = bufio.NewWriter(os.Stdout)
)

func init() {
	sc.Split(bufio.ScanWords)
}

func next() string {
	sc.Scan()
	return sc.Text()
}

func nextInt() int {
	var x int
	fmt.Sscan(next(), &x)
	return x
}

func nextInt64() int64 {
	var x int64
	fmt.Sscan(next(), &x)
	return x
}

func nextFloat64() float64 {
	var x float64
	fmt.Sscan(next(), &x)
	return x
}

func printlnInt(x int) {
	fmt.Fprintln(wr, x)
}

func printlnStr(s string) {
	fmt.Fprintln(wr, s)
}

func flush() {
	wr.Flush()
}

func main() {
	n := nextInt()
	k := nextInt()

	if n%k == 0 {
		fmt.Println(0)
	} else {
		fmt.Println(1)
	}

	flush()
}
