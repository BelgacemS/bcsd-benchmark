package main 

import "fmt"


func main() {                
	var n,k uint8 
	fmt.Scan(&n,&k)

	if n % k == 0{
		fmt.Print(0)
	}else {
		fmt.Print(1)
	}


}
