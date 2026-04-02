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

	d, g := InputInt(), InputInt()
	p, c := make([]int, d), make([]int, d)
	for i := 0; i < d; i++ {
		p[i], c[i] = InputInt(), InputInt()
	}

	ans := inf
	for bit := 0; bit < (1 << d); bit++ {
		score, tans := 0, 0
		for i := 0; i < d; i++ {
			if 0 < (bit>>i)&1 {
				score += 100*(i+1)*p[i] + c[i]
				tans += p[i]
			}
		}
		if g <= score {
			ans = Min(ans, tans)
			continue
		}
		if bit == 24 {
		}
		for i := d - 1; 0 <= i; i-- {
			if (bit>>i)&1 == 0 {
				point := 100 * (i + 1)
				slv := Min(p[i]-1, (g-score+point-1)/point)
				score += 100 * (i + 1) * slv
				tans += slv
				if bit == 24 {
				}
			}
			if g <= score {
				break
			}
		}
		if g <= score {
			ans = Min(ans, tans)
		}
	}
	OutInt(ans)
}

func Min(a, b int) int {
	if a < b {
		return a
	} else {
		return b
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
