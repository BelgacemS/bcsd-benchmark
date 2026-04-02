package main

import (
	"bufio"
	. "fmt"
	"io"
	"os"
	_ "runtime/debug"
)

// func init() { debug.SetGCPercent(-1) }

func Run(_r io.Reader, _w io.Writer) {
	in := bufio.NewReader(_r)
	out := bufio.NewWriter(_w)
	defer out.Flush()

	var n int
	Fscan(in, &n)
	if n == 0 {
		Fprintln(out, 0)
		return
	}
	a := make([]int, 99999999)
	top := 0
	for n != 0 {
		top++
		a[top] = abs(n % (-2))
		n = (n - a[top]) / (-2)
	}
	for i := top; i >= 1; i-- {
		Fprint(out, a[i])
	}
}

func main() {
	Run(os.Stdin, os.Stdout)
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}
