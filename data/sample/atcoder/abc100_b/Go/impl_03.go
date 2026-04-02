package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	in := bufio.NewReader(os.Stdin)
	var D, N int64
	if _, err := fmt.Fscan(in, &D, &N); err != nil {
		return
	}

	base := int64(1)
	for i := int64(0); i < D; i++ {
		base *= 100
	}

	k := N + (N-1)/99

	ans := base * k
	fmt.Println(ans)
}
