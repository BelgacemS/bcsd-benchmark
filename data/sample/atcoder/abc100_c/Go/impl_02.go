package main

/*** import ***/
import (
	"bufio"
	"os"
	"strconv"

	"fmt"

	"math"
)

/*** type ***/
type Numeric interface {
	~int | ~int8 | ~int16 | ~int32 | ~int64 |
		~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64
}

/*** const ***/
const (
	BufSize int = 300001
)

/*** var ***/
var sc = bufio.NewScanner(os.Stdin)
var wr = bufio.NewWriter(os.Stdout)

/*** func ***/

func main() {
	defer wr.Flush()
	sc.Buffer(make([]byte, BufSize), math.MaxInt32)
	sc.Split(bufio.ScanWords)

	//
	N := scanI()
	a := make([]int, N)
	for i := range N {
		a[i] = scanI()
	}

	cnt := 0
	for i := range N {
		for a[i]%2 == 0 {
			a[i] /= 2
			cnt++
		}
	}
	fmt.Fprintln(wr, cnt)
}

/*** methods ***/
func scanI() int {
	sc.Scan()
	num, err := strconv.Atoi(sc.Text())
	if err != nil {
		panic(err)
	}
	return num
}

func scanF() float64 {
	sc.Scan()
	num, err := strconv.ParseFloat(sc.Text(), 64)
	if err != nil {
		panic(err)
	}
	return num
}

func scanS() string {
	sc.Scan()
	return sc.Text()
}

func max[N Numeric](a, b N) N {
	if a > b {
		return a
	}
	return b
}

func min[N Numeric](a, b N) N {
	if a < b {
		return a
	}
	return b
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}
