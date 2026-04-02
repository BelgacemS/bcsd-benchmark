package main

import (
	"bufio"
	"fmt"
	"os"
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

	s, t := InputString(), InputString()
	n := len(s)
	flag := false
	for i := 0; i < n; i++ {
		u := s[i:n] + s[0:i]
		if t == u {
			flag = true
		}
	}
	if flag {
		fmt.Fprintln(wt, "Yes")
	} else {
		fmt.Fprintln(wt, "No")
	}

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
