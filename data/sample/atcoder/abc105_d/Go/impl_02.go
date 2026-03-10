package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
)

var sc, wr = bufio.NewScanner(os.Stdin), bufio.NewWriter(os.Stdout)

func scanString() string {
	sc.Scan()
	return sc.Text()
}

func scanRunes() []rune {
	return []rune(scanString())
}

func scanInt() int {
	x, _ := strconv.Atoi(scanString())
	return x
}

func scanInt64() int64 {
	x, _ := strconv.ParseInt(scanString(), 10, 64)
	return x
}

func scanFloat() float64 {
	x, _ := strconv.ParseFloat(scanString(), 64)
	return x
}

func scanInts(n int) []int {
	a := make([]int, n)
	for i := 0; i < n; i++ {
		a[i] = scanInt()
	}
	return a
}

func debug(a ...any) {
	if os.Getenv("ONLINE_JUDGE") == "false" {
		fmt.Fprintln(os.Stderr, a...)
	}
}

func abs(a int) int {
	if a < 0 {
		return -a
	} else {
		return a
	}
}

func min(a, b int) int {
	if a < b {
		return a
	} else {
		return b
	}
}

func max(a, b int) int {
	if a < b {
		return b
	} else {
		return a
	}
}

func main() {
	defer wr.Flush()
	sc.Split(bufio.ScanWords)
	sc.Buffer(make([]byte, 1e4), 1e7)

	solve()
}

/*
Solve the problem here
*/

type Range struct {
	l int
	r int
}

func solve() {
	N := scanInt()
	M := scanInt()
	A := scanInts(N)

	f := make(map[int]int)
	f[0] = 1
	ans := 0
	cur := 0
	for _, x := range A {
		cur = (cur + x) % M
		ans += f[cur]
		f[cur]++
	}
	fmt.Println(ans)
}
