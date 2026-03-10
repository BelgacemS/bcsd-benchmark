// https://atcoder.jp/contests/abc104/tasks/abc104_b

package main

import (
	"bufio"
	"fmt"
	"math"
	"os"
	"strconv"
	"strings"
)

var scanner = bufio.NewScanner(os.Stdin)

func init() {
	scanner.Buffer([]byte{}, math.MaxInt64)
}

func main() {
	s := nextString()

	var hasC bool
	for i, c := range s {
		switch {
		case i == 0:
			if c != 'A' {
				fmt.Println("WA")
				return
			}
		case i < 2:
			if c < 'a' || c > 'z' {
				fmt.Println("WA")
				return
			}
		case i <= len(s)-2:
			if c == 'C' {
				if hasC {
					fmt.Println("WA")
					return
				}
				hasC = true
			} else {
				if c < 'a' || c > 'z' {
					fmt.Println("WA")
					return
				}
			}
		default:
			if c < 'a' || c > 'z' {
				fmt.Println("WA")
				return
			}
		}
	}

	if hasC {
		fmt.Println("AC")
	} else {
		fmt.Println("WA")
	}
}

func nextInt() int {
	scanner.Scan()
	i, _ := strconv.Atoi(scanner.Text())
	return i
}

func nextIntList() []int {
	scanner.Scan()
	var list []int
	for _, s := range strings.Split(scanner.Text(), " ") {
		i, _ := strconv.Atoi(s)
		list = append(list, i)
	}
	return list
}

func nextString() string {
	scanner.Scan()
	return scanner.Text()
}
