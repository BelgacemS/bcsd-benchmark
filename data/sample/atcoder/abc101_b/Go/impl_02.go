package main

import (
	"fmt"
	"strconv"
	"strings"
)


func main() {
	var Ns string
	fmt.Scan(&Ns)
	
	var SN int
	for _, ni := range strings.Split(Ns, "") {
		i, _ := strconv.Atoi(ni)
		SN += i
	}

	N, _ := strconv.Atoi(Ns)
	ans := "No"
	if N % SN == 0 {
		ans = "Yes"
	}

	fmt.Println(ans)
}
