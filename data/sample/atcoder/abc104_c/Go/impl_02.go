package main

import (
	"fmt"
	"math"
)

func main() {
	var d, g int
	fmt.Scanf("%d %d", &d, &g)
	p := make([]int, d)
	c := make([]int, d)
	for i := 0; i < d; i++ {
		var pv, cv int
		fmt.Scanf("%d %d", &pv, &cv)
		p[i] = pv
		c[i] = cv
	}

	var num int = math.MaxInt

	// 1 << d とすれば、例えばd=10の場合、1を10ビットシフトするので、1が11桁目までシフトされる。
	// すると、2進数で 10000000000 なのでそれ未満ということはつまり 1111111111 で10桁の最大値となる。
	// maskはその得点におけるボーナス点を取るかどうか（全問回答するかどうか）の全組み合わせ。
	for mask := 0; mask < (1 << d); mask++ {
		// 下位得点から見ていく
		var restMax int
		var score int
		var cnt int
		for i := 0; i < d; i++ {
			if mask&(1<<i) != 0 {
				// i問目全回答
				s := 100*(i+1)*p[i] + c[i]
				score += s
				cnt += p[i]
			} else {
				restMax = i
			}
		}
		// fmt.Println(cnt, score, mask)
		// restMaxには全回答しなかったもので、最大桁目が入っている。
		// これで残りのスコアを埋められるのかを考える。
		if score < g {
			// 上記全回答パターンで届かなかった。
			// 1 ~ p[i]-1 個の回答で届くのか検証
			// （0はありえないのは、その下の桁で埋めるのと、ここで埋めるのでは回答数的に同義だから）
			// （また同様にp[i]もありえない。p[i]を含めるとイコール全回答になってしまうから）
			needScore := g - score
			point := 100 * (restMax + 1)
			needCnt := (needScore + point - 1) / point // 余りを切り上げる方法
			if needCnt >= p[restMax] {
				continue
			}
			cnt += needCnt
		}
		num = int(math.Min(float64(num), float64(cnt)))
	}
	fmt.Println(num)
}
