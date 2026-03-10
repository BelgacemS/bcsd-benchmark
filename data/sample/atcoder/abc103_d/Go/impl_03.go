package main

import (
	"bufio"
	"fmt"
	"os"
	"sort"
	"strconv"
)

var (
	sc = bufio.NewScanner(os.Stdin)
	wt = bufio.NewWriter(os.Stdout)
)

const (
	inf = 1 << 60
	MOD = 998244353
)

func main() {
	/*** INIT ***/
	defer wt.Flush()
	sc.Buffer([]byte{}, inf)
	sc.Split(bufio.ScanWords)

	_, m := InputInt(), InputInt()
	v := make([]pair, m)
	for i := 0; i < m; i++ {
		v[i].first = InputInt()
		v[i].second = InputInt()
	}
	sort.Slice(v, func(i, j int) bool {
		return v[i].second < v[j].second
	})

	ans := 0
	now := 0
	for i := 0; i < m; i++ {
		if now < v[i].first {
			ans++
			now = v[i].second - 1
		}
	}
	OutInt(ans)
}

type pair struct {
	first  int
	second int
}

/*** I/O ***/
func InputInt() int {
	sc.Scan()
	val, _ := strconv.Atoi(sc.Text())
	return val
}

func InputString() string {
	sc.Scan()
	return sc.Text()
}

func OutInt(val int) {
	fmt.Fprintln(wt, val)
}

func OutString(s string) {
	fmt.Fprintln(wt, s)
}
