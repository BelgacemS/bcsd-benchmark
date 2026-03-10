// LUOGU_RID: 201597244
package main

import (
	"bufio"
	. "fmt"
	"io"
	"os"
	"sort"
)

type node struct {
	x, y, z int
}

func run(in io.Reader, out io.Writer) {
	var n, m int
	Fscan(in, &n, &m)
	a := make([]struct {
		x, y, z int
	}, n)
	for i := range a {
		Fscan(in, &a[i].x, &a[i].y, &a[i].z)
	}
	ans := 0
	for i := 1; i > -2; i -= 2 {
		for j := 1; j > -2; j -= 2 {
			for k := 1; k > -2; k -= 2 {
				sort.Slice(a, func(_i, _j int) bool {
					return a[_i].x*i+a[_i].y*j+a[_i].z*k > a[_j].x*i+a[_j].y*j+a[_j].z*k
				})
				p := 0
				for _, s := range a[:m] {
					p += s.x*i + s.y*j + s.z*k
				}
				ans = max(ans, p)
			}
		}

	}
	Fprintln(out, ans)
}
func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}
func main() { run(bufio.NewReader(os.Stdin), os.Stdout) }
func max(a, b int) int {
	if b > a {
		return b
	}
	return a
}
