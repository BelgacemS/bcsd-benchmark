package main

import (
	"bufio"
	"container/heap"
	"fmt"
	"os"
	"strconv"
	"strings"
)

// ある(Aru)'sテクログ
// Go言語でAtCoder｜スタック、キュー、 優先キューの実装方法
// より一部引用

type pqi struct{ x []int }

type priorityQueue []pqi

func (pq priorityQueue) Len() int      { return len(pq) }
func (pq priorityQueue) Swap(i, j int) { pq[i], pq[j] = pq[j], pq[i] }
func (pq priorityQueue) Less(i, j int) bool {
	if pq[i].x[0] == pq[j].x[0] {
		return pq[i].x[1] < pq[j].x[1]
	} else {
		return pq[i].x[0] < pq[j].x[0]
	}
}
func (pq *priorityQueue) Push(x interface{}) { *pq = append(*pq, x.(pqi)) }
func (pq *priorityQueue) Pop() interface{} {
	x := (*pq)[len(*pq)-1]
	*pq = (*pq)[0 : len(*pq)-1]
	return x
}

func min (a int, b int) int {
  if a > b {
    return b
  }
  return a
}

func main() {
	var (
		INF int = 1009

		D int
		G int

		problems [][]int

		answer int = INF
	)

	sc := bufio.NewScanner(os.Stdin)

	sc.Scan()
	inputs := strings.Split(sc.Text(), " ")

	D, _ = strconv.Atoi(inputs[0])
	G, _ = strconv.Atoi(inputs[1])

	problems = make([][]int, D)

	for i := 0; i < D; i++ {
		sc.Scan()
		inputs := strings.Split(sc.Text(), " ")

		p, _ := strconv.Atoi(inputs[0])
		c, _ := strconv.Atoi(inputs[1])

		problems[i] = []int{p, c}
	}

	for bits := 0; bits < (1 << D); bits++ {
		total_score := 0
		remain_problem_nums := make([]int, D)
		pq := priorityQueue{}
		solved_problem_cnt := 0

		for i := 0; i < D; i++ {
			if (bits>>i)&1 == 1 {
				total_score += 100*(i+1)*problems[i][0] + problems[i][1]
				remain_problem_nums[i] = problems[i][0] - 1
				heap.Push(&pq, pqi{[]int{problems[i][1] + 100*(i+1), i}})
				solved_problem_cnt += problems[i][0]
			}
		}

		if total_score >= G {
			for total_score > G {
				q := heap.Pop(&pq).(pqi)
				total_score -= q.x[0]
				solved_problem_cnt--

				if total_score <= G {
					if total_score < G {
						total_score += q.x[0]
						solved_problem_cnt++
					}

					break
				}

				if remain_problem_nums[q.x[1]] > 0 {
					heap.Push(&pq, pqi{[]int{100 * (q.x[1] + 1), q.x[1]}})
					remain_problem_nums[q.x[1]]--
				}
			}

			answer = min(answer, solved_problem_cnt)
		}
	}

	fmt.Println(answer)
}
