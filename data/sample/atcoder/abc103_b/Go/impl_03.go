package main

import(
    "fmt"
    "os"
)

func main() {
	var S ,T string
    fmt.Scan(&S)
    fmt.Scan(&T)

    for i:=0;i<len(S);i++{
        tmp:=string(S[len(S)-i-1:])+string(S[0:len(S)-i-1])
        if tmp==T{
            fmt.Println("Yes")
            os.Exit(0)
        }
    }
    fmt.Println("No")
}
