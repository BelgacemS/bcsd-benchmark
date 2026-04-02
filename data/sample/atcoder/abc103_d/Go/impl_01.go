package main

import (
	"bufio"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"
)

func main() {
	var (
		M int

		intervals                [][]int
		most_right_broken_bridge int = -1

		answer int = 0
	)

	sc := bufio.NewScanner(os.Stdin)

	sc.Scan()
	inputs := strings.Split(sc.Text(), " ")

	M, _ = strconv.Atoi(inputs[1])

	intervals = make([][]int, M)

	for i := 0; i < M; i++ {
		sc.Scan()
		inputs := strings.Split(sc.Text(), " ")

		a, _ := strconv.Atoi(inputs[0])
		b, _ := strconv.Atoi(inputs[1])

		intervals[i] = []int{a, b}
	}

	sort.Slice(intervals, func(i, j int) bool { return intervals[i][1] < intervals[j][1] })

	for i := 0; i < M; i++ {
		if most_right_broken_bridge < intervals[i][0] {
			answer++
			most_right_broken_bridge = intervals[i][1] - 1
		}
	}

	fmt.Println(answer)
}
