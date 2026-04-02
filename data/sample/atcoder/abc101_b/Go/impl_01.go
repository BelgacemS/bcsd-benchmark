package main

import (
	"fmt"
	"strconv"
	"strings"
)

func main() {
	var n int
	fmt.Scanf("%d", &n)

	sn := fmt.Sprint(n) //12
	var sum int
	var sumtemp int
	slice := strings.Split(sn, "")
	for _, v := range slice {
		sumtemp, _ = strconv.Atoi(v)
		sum += sumtemp

	}

	if n%sum == 0 {
		fmt.Println("Yes")
	} else {
		fmt.Println("No")
	}

}
