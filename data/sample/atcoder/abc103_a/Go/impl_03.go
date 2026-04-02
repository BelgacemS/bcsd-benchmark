package main
import "fmt"
func abs(v int) int {
	if v > 0 {
		return v
	} else {
		return -v
	}
}
func sum(arr []int) int {
	s := 0
	for _, v := range arr {
		s += v
	}
	return s
}
func max(arr []int) int {
	m := arr[0]
	for _, v := range arr {
		if m < v {
			m = v
		}
	}
	return m
}
func main() {
	var a1, a2, a3 int
	fmt.Scan(&a1, &a2, &a3)
	arr := []int{abs(a1 - a2), abs(a2 - a3), abs(a3 - a1)}
	fmt.Println(sum(arr) - max(arr))
}