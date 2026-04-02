package main

import (
	"bufio"
	"fmt"
	"math"
	"math/big"
	"math/bits"
	"os"
	"reflect"
	"runtime"
	"sort"
	"strconv"
	"strings"

	"golang.org/x/exp/constraints"
	"golang.org/x/exp/maps"
	"golang.org/x/exp/slices"
)

var p10 []int
var rdr *bufio.Scanner
var wtr *bufio.Writer
var wtrErr *bufio.Writer

// DebugMode デバック出力設定
var DebugMode = true //trueかつ環境変数にDebugが設定されていること
var DebugOut = 2     //1:stdout 2:stderr

const (
	BUFSIZE                = 10000000
	MOD2305843009213693951 = 2305843009213693951
	MOD1000000007          = 1000000007
	MOD998244353           = 998244353
	MOD                    = MOD998244353
	INF                    = 1 << 60
)

func solve() {
	n, m := ri2()
	a := ris(n)
	b := make([]int, n)
	b[0] = a[0] % m
	for i := 1; i < len(a); i++ {
		b[i] = (b[i-1] + a[i]) % m
	}
	cm := make(map[int]int)
	for i := 0; i < len(b); i++ {
		cm[b[i]]++
	}
	ans := 0
	cm[0]++
	for _, v := range cm {
		if v <= 1 {
			continue
		}
		ans += v * (v - 1) / 2
	}
	out(ans)
}

func flush() {
	wtr.Flush()
	wtrErr.Flush()
}
func main() {
	defer flush()
	rdr = bufio.NewScanner(os.Stdin)
	rdr.Buffer(make([]byte, 4096), math.MaxInt64)
	rdr.Split(bufio.ScanWords)
	wtr = bufio.NewWriterSize(os.Stdout, BUFSIZE)
	wtrErr = bufio.NewWriterSize(os.Stderr, BUFSIZE)
	p10 = []int{1, 10, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000, 1000000000, 10000000000, 100000000000, 1000000000000, 10000000000000, 100000000000000, 1000000000000000, 10000000000000000, 100000000000000000, 1000000000000000000}
	DebugEnv := CheckEnvVarExists("DEBUG")
	if !DebugEnv {
		DebugMode = false
	}
	solve()
}

// 出力
func out(a ...interface{}) {
	str := fmt.Sprintln(a...)
	_, err := wtr.WriteString(str)
	if err != nil {
		return
	}
	return
}
func outE(a ...interface{}) {
	str := fmt.Sprintln(a...)
	_, err := wtrErr.WriteString(str)
	if err != nil {
		return
	}
	return
}
func outf(f float64) {
	outfmt("%0.9f\n", f)
}
func outn(x int) {
	outfmt("%d ", x)
}
func outfn(f float64) {
	outfmt("%0.9f ", f)
}
func outfmt(format string, a ...interface{}) (int, error) {
	str := fmt.Sprintf(format, a...)
	return wtr.WriteString(str)
}
func outListX(l []int) {
	s := make([]string, 0, len(l))
	for i := 0; i < len(l); i++ {
		s = append(s, strconv.Itoa(l[i]))
	}
	write(strings.Join(s, " "))
}
func outListY(l []int) {
	s := make([]string, 0, len(l))
	for i := 0; i < len(l); i++ {
		s = append(s, strconv.Itoa(l[i]))
	}
	write(strings.Join(s, "\n"))
}
func outYN(x bool) {
	if x == true {
		out("Yes")
	} else {
		out("No")
	}
}

var DebugColor = colorGreen

const (
	colorRed     = "\033[31m"
	colorGreen   = "\033[32m"
	colorYellow  = "\033[33m"
	colorBlue    = "\033[34m"
	colorMagenta = "\033[35m"
	colorCyan    = "\033[36m"
	colorReset   = "\033[0m"
)

func dbg(s ...interface{}) {
	if DebugMode == false {
		return
	}
	DebugColor = colorRed
	pc, _, line, ok := runtime.Caller(1)
	if ok {
		funcName := runtime.FuncForPC(pc).Name()
		t := fmt.Sprintf("%s%s:%d:%s%s%s%s", colorGreen, funcName, line, colorReset, DebugColor, fmt.Sprint(s...), colorReset)
		if DebugOut == 1 {
			out(t)
		} else if DebugOut == 2 {
			outE(t)
		}
	}
}

func dbgc(c string, s ...interface{}) {
	if DebugMode == false {
		return
	}
	pc, _, line, ok := runtime.Caller(1)
	if ok {
		funcName := runtime.FuncForPC(pc).Name()
		t := fmt.Sprintf("%s:%d: %s%s%s", funcName, line, c, s, colorReset)
		if DebugOut == 1 {
			out(t)
		} else if DebugOut == 2 {
			outE(t)
		}
	}
}

func CheckEnvVarExists(key string) bool {
	_, exists := os.LookupEnv(key)
	return exists
}
func write(s string) {
	_, err := wtr.WriteString(s)
	if err != nil {
		return
	}
	_, err = wtr.WriteString("\n")
	if err != nil {
		return
	}
	return
}

// 入力
func rs() string { rdr.Scan(); return rdr.Text() }
func ri() int {
	rdr.Scan()
	i, e := strconv.Atoi(rdr.Text())
	if e != nil {
		panic(e)
	}
	return i
}
func ri2() (int, int) {
	a := ri()
	b := ri()
	return a, b
}
func ri3() (int, int, int) {
	a := ri()
	b := ri()
	c := ri()
	return a, b, c
}
func ri4() (int, int, int, int) {
	a := ri()
	b := ri()
	c := ri()
	d := ri()
	return a, b, c, d
}
func ris(n int) []int {
	res := make([]int, n)
	for i := 0; i < n; i++ {
		res[i] = ri()
	}
	return res
}
func riy(n int) []int {
	ret := make([]int, 0)
	for i := 0; i < n; i++ {
		ret = append(ret, ri())
	}
	return ret
}
func risapp(a []int, n int) []int {
	for i := 0; i < n; i++ {
		a = append(a, ri())
	}
	return a
}
func ris2(n int) ([]int, []int) {
	res := make([]int, n)
	res2 := make([]int, n)
	for i := 0; i < n; i++ {
		res[i] = ri()
		res2[i] = ri()
	}
	return res, res2
}
func rf() float64 {
	f, e := strconv.ParseFloat(rs(), 64)
	if e != nil {
		panic(e)
	}
	return f
}
func rfs(n int) []float64 {
	res := make([]float64, n)
	for i := 0; i < n; i++ {
		res[i] = rf()
	}
	return res
}
func rss(n int) []string {
	res := make([]string, n)
	for i := 0; i < n; i++ {
		res[i] = rs()
	}
	return res
}
func readIntLines(h, w int) [][]int {
	l := make([][]int, h)
	for i := 0; i < h; i++ {
		l[i] = ris(w)
	}
	return l
}

func readEdges(m int, readWeight bool) []Edge {
	ret := make([]Edge, m)
	for i := 0; i < m; i++ {
		a, b := ri2()
		ret[i].from = a
		ret[i].to = b
		ret[i].w = 1
		if readWeight == true {
			ret[i].w = ri()
		}
	}
	return ret
}
func readPairs(m int) []Pair {
	ret := make([]Pair, m)
	for i := 0; i < m; i++ {
		a, b := ri2()
		ret[i] = Pair{a, b}
	}
	return ret
}
func checkEnvVarExists(key string) bool {
	_, exists := os.LookupEnv(key)
	return exists
}

// 汎用関数
func itoa(x int) string {
	return strconv.Itoa(x)
}
func atoi(s string) int {
	n, _ := strconv.Atoi(s)
	return n
}
func cond[T any](t bool, a, b T) T {
	if t == true {
		return a
	} else {
		return b
	}
}
func abs[T constraints.Signed](a T) T               { return cond(a >= 0, a, -a) }
func max[T constraints.Ordered](a, b T) T           { return cond(a >= b, a, b) }
func min[T constraints.Ordered](a, b T) T           { return cond(a < b, a, b) }
func vals[M ~map[K]V, K comparable, V any](m M) []V { return maps.Values(m) }
func keys[M ~map[K]V, K comparable, V any](m M) []K { return maps.Keys(m) }
func cs[S ~[]E, E any](s S) S                       { return slices.Clone(s) }
func cs2[S ~[][]E, E any](s S) S {
	ret := make(S, len(s))
	for i := 0; i < len(s); i++ {
		ret[i] = slices.Clone(s[i])
	}
	return ret
}
func chmin[T constraints.Ordered](a *T, b T) {
	if *a > b {
		*a = b
	}
}
func chmax[T constraints.Ordered](a *T, b T) {
	if *a < b {
		*a = b
	}
}
func isInRange(x, low, high int) bool {
	return low <= x && x <= high
}
func isOutRange(x, low, high int) bool {
	return !isInRange(x, low, high)
}
func maxSlice[T constraints.Ordered](l []T) T {
	ret := l[0]
	for i := 1; i < len(l); i++ {
		if ret < l[i] {
			ret = l[i]
		}
	}
	return ret
}
func minSlice[T constraints.Ordered](l []T) T {
	ret := l[0]
	for i := 1; i < len(l); i++ {
		if ret > l[i] {
			ret = l[i]
		}
	}
	return ret
}
func maxSliceIdx[T constraints.Ordered](l []T) int {
	idx := 0
	for i := 0; i < len(l); i++ {
		if l[idx] < l[i] {
			idx = i
		}
	}
	return idx
}
func minSliceIdx[T constraints.Ordered](l []T) int {
	idx := 0
	for i := 0; i < len(l); i++ {
		if l[idx] > l[i] {
			idx = i
		}
	}
	return idx
}
func removeAt[T any](s []T, i int) []T {
	return append(s[:i], s[i+1:]...)
}
func insertAfter[T any](s []T, i int, v T) []T {
	if i < 0 || i >= len(s) {
		return append(s, v) // 範囲外なら末尾に追加
	}
	s = append(s[:i+1], append([]T{v}, s[i+1:]...)...)
	return s
}
func insertBefore[T any](s []T, i int, v T) []T {
	newS := make([]T, 0, len(s)+1)
	if i <= 0 {
		return append([]T{v}, s...)
	}
	if i >= len(s) {
		newS = append(newS, s...)
		return append(newS, v) // 範囲外 → 末尾に追加
	}
	newS = append(newS, s[:i]...)
	newS = append(newS, v)
	newS = append(newS, s[i:]...)
	return newS
}

func newMaps[K comparable, V any](n int) []map[K]V {
	ret := make([]map[K]V, n)
	for i := 0; i < n; i++ {
		ret[i] = make(map[K]V)
	}
	return ret
}

// Mapの要素の最大値とそのキー(１個)を返す
func maxMapElem[M ~map[K]V, K comparable, V constraints.Ordered](m M) (K, V) {
	first := true
	var key K
	var val V
	for i, v := range m {
		if first == true {
			key = i
			val = v
			first = false
			continue
		}
		if v > val {
			val = v
			key = i
		}
	}
	return key, val
}

// Mapの要素の最小値とそのキー(１個)を返す
func maxMinElem[M ~map[K]V, K comparable, V constraints.Ordered](m M) (K, V) {
	first := true
	var key K
	var val V
	for i, v := range m {
		if first == true {
			key = i
			val = v
			first = false
			continue
		}
		if v < val {
			val = v
			key = i
		}
	}
	return key, val
}

// スライスの昇順のorderを返す
func sliceOrder(a []int) []int {
	bp := make([]Pair, len(a))
	for i := 0; i < len(a); i++ {
		bp[i] = Pair{a[i], i}
	}
	rank := make([]int, len(a))
	sort.Slice(bp, func(i, j int) bool {
		return bp[i].a < bp[j].a
	})
	for i := 0; i < len(bp); i++ {
		rank[i] = bp[i].b
	}
	return rank
}

// スライスの最大値
func maxVals[T constraints.Ordered](x ...T) T { return maxSlice(x) }

// スライスの最小値
func minVals[T constraints.Ordered](x ...T) T { return minSlice(x) }

// 「x / y」を切り上げた整数を返す関数。 符号が同じ場合、(x+y-1)/y によって切り上げ。
func ceilDiv(x, y int) int {
	if y == 0 {
		panic("divide by zero")
	}
	if (x^y) > 0 && x%y != 0 {
		return x/y + 1
	}
	return x / y
}

// 「x / y」を切り捨てた整数を返す 。符号が異なる場合、余りがあれば 1 小さくして切り捨て
func floorDiv(x, y int) int {
	if y == 0 {
		panic("divide by zero")
	}
	if (x^y) < 0 && x%y != 0 {
		return x/y - 1
	}
	return x / y
}

// Grid操作(prefixはgridで統一)

// gridの読み込み
func gridRead(h int) [][]byte {
	g := make([][]byte, h)
	for i := 0; i < h; i++ {
		g[i] = []byte(rs())
	}
	return g
}

// gridの表示
func gridOut[T any](row []T) {
	for _, v := range row {
		switch val := any(v).(type) {
		case []byte:
			fmt.Println(string(val))
		default:
			fmt.Println(val)
		}
	}
}

// grid範囲内かどうかのチェッカー関数
func gridRangeChecker(aMin, aMax, bMin, bMax int) func(Pair) bool {
	f := func(p Pair) bool {
		return isInRange(p.a, aMin, aMax) && isInRange(p.b, bMin, bMax)
	}
	return f
}

// gridに番兵を追加する
func gridWall[T comparable](g [][]T, w T) [][]T {
	head := newSlice[T](len(g[0])+2, w)
	tail := newSlice[T](len(g[0])+2, w)
	for i := 0; i < len(g); i++ {
		g[i] = append([]T{w}, g[i]...)
		g[i] = append(g[i], w)
	}
	g = append([][]T{head}, g...)
	g = append(g, tail)
	return g
}

func dxy(c byte) Pair {
	switch c {
	case 'U':
		return Pair{-1, 0}
	case 'D':
		return Pair{1, 0}
	case 'L':
		return Pair{0, -1}
	case 'R':
		return Pair{0, 1}
	}
	return Pair{0, 0}
}

// 2次元Grid初期化
func gridInit[T constraints.Ordered](h, w int, ch T) [][]T {
	return newSlice2[T](h, w, ch)
}

// 　2次元スライスを時計回り0,90,180,270度,y軸反転,x軸反転させる
func gridRotate[S ~[][]T, T constraints.Ordered](g S, rotation int, flipY, flipX bool) S {
	h := len(g)
	w := len(g[0])
	var ret S
	var zero T
	if rotation == 1 || rotation == 3 {
		ret = gridInit[T](w, h, zero)
	} else {
		ret = gridInit[T](h, w, zero)
	}
	conv := gridPosConv(h, w, rotation, flipY, flipX)
	for i := 0; i < h; i++ {
		for j := 0; j < w; j++ {
			ch := g[i][j]
			ni, nj := conv(i, j)
			ret[ni][nj] = ch
		}
	}
	return ret
}

// 座標{y,x}について時計回り0,90,180,270度,y軸反転,x軸反転するクロージャーをかえす
func gridPosConv(maxY, maxX, rotation int, flipY, flipX bool) func(int, int) (int, int) {
	return func(y, x int) (int, int) {
		if flipY {
			y = maxY - 1 - y
		}
		if flipX {
			x = maxX - 1 - x
		}
		switch rotation % 4 {
		case 1:
			y, x = x, maxY-1-y
		case 2:
			y, x = maxY-1-y, maxX-1-x
		case 3:
			y, x = maxX-1-x, y
		}
		return y, x
	}
}

// {y,x}から高さheight,幅widthの範囲を切り出す
func gridClip[S ~[][]T, T any](grid S, y, x, height, width int) S {
	if y < 0 || x < 0 || y+height > len(grid) || x+width > len(grid[0]) {
		panic("The provided range is out of grid bounds.")
	}
	clipped := make(S, height)
	for i := range clipped {
		clipped[i] = make([]T, width)
	}
	for i := 0; i < height; i++ {
		for j := 0; j < width; j++ {
			clipped[i][j] = grid[y+i][x+j]
		}
	}
	return clipped
}

// copyFromをcopyToの{y,x}の位置にコピーする
func gridPaste[T constraints.Ordered](copyTo, copyFrom [][]T, y, x int) {
	if y < 0 || x < 0 || y+len(copyFrom) > len(copyTo) || x+len(copyFrom[0]) > len(copyTo[0]) {
		panic("The provided range is out of original grid bounds.")
	}
	for i := range copyFrom {
		for j := range copyFrom[i] {
			copyTo[y+i][x+j] = copyFrom[i][j]
		}
	}
}

// {y,x}から高さheight,幅widthの範囲について、y軸またはx軸反転させる
func gridFlip[T constraints.Ordered](original [][]T, y, x, height, width int, flipY, flipX bool) {
	extracted := gridClip(original, y, x, height, width)
	flipped := gridRotate(extracted, 0, flipY, flipX)
	gridPaste(original, flipped, y, x)
}

// subgridがgridに部分一致するかeval()で評価する
func gridMatch[T constraints.Ordered](grid [][]T, y, x int, subgrid [][]T, eval func(T, T) bool) bool {
	//eval例:
	//func(a,b byte)bool{return  a == b || a == '?' || b == '?'}
	if y+len(subgrid) > len(grid) || x+len(subgrid[0]) > len(grid[0]) {
		return false
	}
	for i := range subgrid {
		for j := range subgrid[i] {
			if !eval(grid[y+i][x+j], subgrid[i][j]) {
				return false
			}
		}
	}
	return true
}

// []stringを[][]byteに変換する
func gridConv(s []string) [][]byte {
	ret := make([][]byte, len(s))
	for i := 0; i < len(s); i++ {
		ret[i] = []byte(s[i])
	}
	return ret
}

// Mod
func modAdd(a, b int) int { return (a + b) % MOD }
func modAdds(x ...int) int {
	cur := 0
	for i := 0; i < len(x); i++ {
		cur = modAdd(cur, x[i])
	}
	return cur
}
func modSub(a, b int) int { return (((a - b) % MOD) + MOD) % MOD }
func modMul(a, b int) int { return (a * b) % MOD }
func modInv(x int) int {
	a, _ := exgcd(x, MOD)
	return (a + MOD) % MOD
}
func sumMod(a []int) int {
	ret := 0
	for i := 0; i < len(a); i++ {
		ret = modAdd(ret, a[i])
	}
	return ret
}

// 2分探索
func UpperBound[T constraints.Ordered](array []T, target T) int {
	low, high, mid := 0, len(array)-1, 0
	for low <= high {
		mid = (low + high) / 2
		if array[mid] > target {
			high = mid - 1
		} else {
			low = mid + 1
		}
	}
	return low
}
func LowerBound[T constraints.Ordered](array []T, target T) int {
	low, high, mid := 0, len(array)-1, 0
	for low <= high {
		mid = (low + high) / 2
		if array[mid] >= target {
			high = mid - 1
		} else {
			low = mid + 1
		}
	}
	return low
}

func rangeCount[T constraints.Ordered](a []T, nmin, nmax T) int {
	return UpperBound(a, nmax) - LowerBound(a, nmin)
}
func rangeCount2[T constraints.Ordered](a []T, idx int, nmin, nmax T) int {
	return max(idx, UpperBound(a, nmax)) - max(idx, LowerBound(a, nmin))
}
func searchNearestNum(a []int, x int) int {
	k := LowerBound(a, x)
	if k == len(a) {
		return a[k-1]
	}
	if k == 0 {
		return a[0]
	}
	if abs(a[k]-x) > abs(a[k-1]-x) {
		return a[k-1]
	} else {
		return a[k]
	}
}
func countIntervalLen(a []int, x, lowerLimit, higherLimit int) int {
	idx := UpperBound(a, x)
	low := lowerLimit
	high := higherLimit
	if idx != 0 {
		low = a[idx-1]
	}
	if idx != len(a) {
		high = a[idx]
	}
	return high - low - 1
} // 昇順ソート済みの[]intについて指定した数値の前後要素の区間を求める
func searchPairsRange(p []Pair, l, r int) (int, int) {
	ret := sort.Search(len(p), func(i int) bool {
		return l < p[i].a
	})
	if ret != 0 && l < p[ret-1].b {
		ret--
	}
	ret2 := sort.Search(len(p), func(i int) bool {
		return r < p[i].b
	})
	if ret2 != len(p) && p[ret2].a > r {
		ret2--
	}
	chmax(&ret, 0)
	chmax(&ret2, 0)
	chmin(&ret, len(p)-1)
	chmin(&ret2, len(p)-1)
	chmin(&ret, ret2)
	return ret, ret2
} // 昇順の重複のない区間([]Pair)について区間[l,r]が含まれるindexの範囲を返す

// スライス・map操作系
func sumSlice[T constraints.Integer | constraints.Float](l []T) T {
	var s T
	for i := 0; i < len(l); i++ {
		s += l[i]
	}
	return s
}
func slice2map[M ~map[K]int, K comparable](l []K) map[K]int {
	m := make(map[K]int)
	for i := 0; i < len(l); i++ {
		m[l[i]]++
	}
	return m
}

func reverseSort[T constraints.Ordered](a []T) []T {
	sort.Slice(a, func(i, j int) bool { return a[i] > a[j] })
	return a
}
func reverseList[T any](x []T) []T {
	ret := make([]T, 0, len(x))
	for i := len(x) - 1; i >= 0; i-- {
		ret = append(ret, x[i])
	}
	return ret
}

func haveSameKeys(map1, map2 interface{}) bool {
	val1, val2 := reflect.ValueOf(map1), reflect.ValueOf(map2)
	if val1.Kind() != reflect.Map || val2.Kind() != reflect.Map {
		panic("Both parameters must be maps")
	}
	if val1.Len() != val2.Len() {
		return false
	}
	for _, key := range val1.MapKeys() {
		if val2.MapIndex(key).Kind() == reflect.Invalid {
			return false
		}
	}
	return true
}
func intSliceCnt(a []int, maxRange int) []int {
	ret := intSlice(maxRange, 0)
	for i := 0; i < len(a); i++ {
		ret[a[i]]++
	}
	return ret
}

// DefaultMap デフォルト値付きMap
type DefaultMap[M ~map[K]V, K comparable, V constraints.Ordered] struct {
	m  M
	dv V
}

func NewDefaultMap[M ~map[K]V, K comparable, V constraints.Ordered](dv V) *DefaultMap[M, K, V] {
	ret := DefaultMap[M, K, V]{}
	ret.m = make(M)
	ret.dv = dv
	return &ret
}

func (dm *DefaultMap[M, K, V]) get(key K) V {
	v, ok := dm.m[key]
	if ok == false {
		return dm.dv
	}
	return v
}
func (dm *DefaultMap[M, K, V]) put(key K, val V) {
	dm.m[key] = val
}
func (dm *DefaultMap[M, K, V]) len() int {
	return len(dm.m)
}
func (dm *DefaultMap[M, K, V]) putMin(key K, val V) {
	t := dm.get(key)
	if t > val {
		dm.put(key, val)
	}
}
func (dm *DefaultMap[M, K, V]) putMax(key K, val V) {
	t := dm.get(key)
	if t < val {
		dm.put(key, val)
	}
}
func transpose[T any](matrix [][]T) [][]T {
	if len(matrix) == 0 || len(matrix[0]) == 0 {
		return matrix
	}
	rows := len(matrix)
	cols := len(matrix[0])
	transposeMatrix := make([][]T, cols)
	for i := 0; i < cols; i++ {
		transposeMatrix[i] = make([]T, rows)
		for j := 0; j < rows; j++ {
			transposeMatrix[i][j] = matrix[j][i]
		}
	}
	return transposeMatrix
}
func newSlice[T comparable](n int, v T) []T {
	ret := make([]T, n)
	if ret[0] == v {
		return ret
	}
	for i := 0; i < n; i++ {
		ret[i] = v
	}
	return ret
}
func newSlice2[T comparable](n, n2 int, v T) [][]T {
	ret := make([][]T, n)
	for i := 0; i < n; i++ {
		ret[i] = make([]T, n2)
		if ret[i][0] != v {
			for j := 0; j < n2; j++ {
				ret[i][j] = v
			}
		}
	}
	return ret
}
func newSlice3[T constraints.Ordered | bool](n, n2, n3 int, v T) [][][]T {
	ret := make([][][]T, n)
	for i := 0; i < n; i++ {
		ret[i] = make([][]T, n2)
		for j := 0; j < n2; j++ {
			ret[i][j] = make([]T, n3)
			if ret[i][j][0] != v {
				for k := 0; k < n3; k++ {
					ret[i][j][k] = v
				}
			}
		}
	}
	return ret
}
func intSlice(n, value int) []int {
	return newSlice[int](n, value)
}
func intSlice2(n, n2, v int) [][]int {
	return newSlice2[int](n, n2, v)
}
func intSlice3(n, n2, n3, v int) [][][]int {
	return newSlice3[int](n, n2, n3, v)
}
func rangeSlice(begin, end int) []int {
	ret := make([]int, 0, end-begin+1)
	for i := begin; i <= end; i++ {
		ret = append(ret, i)
	}
	return ret
}

// スライスを時計回りに90度回転する
func rotate90[T any](a [][]T) [][]T {
	w, h := len(a), len(a[0])
	res := make([][]T, h)
	for i := 0; i < h; i++ {
		res[i] = make([]T, w)
		for j := 0; j < w; j++ {
			res[i][j] = a[j][h-i-1]
		}
	}
	return res
}
func i2bs(a []int, add int) []byte {
	ret := make([]byte, len(a))
	for i := 0; i < len(a); i++ {
		ret[i] = byte(a[i] + add)
	}
	return ret
}
func b2is(a []byte, add int) []int {
	ret := make([]int, len(a))
	for i := 0; i < len(a); i++ {
		ret[i] = int(a[i]) + add
	}
	return ret
}
func stringIndexer() (func(string) int, func(int) string) {
	cur := 0
	m := make(map[string]int)
	r := make(map[int]string)
	f := func(s string) int {
		v := m[s]
		if v == 0 {
			cur++
			m[s] = cur
			r[cur] = s
			return cur
		}
		return v
	}
	f2 := func(x int) string {
		return r[x]
	}
	return f, f2
} // 文字列をindexに変換

// 座標を圧縮し、座標変換、逆変換クロージャーを返す
func compressCoordinate(arr []int) ([]int, map[int]int, map[int]int) {
	arrCopy := append([]int(nil), arr...)
	sort.Ints(arrCopy)
	m := make(map[int]int)
	rev := make(map[int]int)
	rank := 0
	for _, a := range arrCopy {
		if _, ok := m[a]; !ok {
			m[a] = rank
			rank++
		}
	}
	result := make([]int, len(arr))
	for i, a := range arr {
		result[i] = m[a]
		rev[i] = a
	}
	return result, m, rev
}

// Pair操作
type Pair struct{ a, b int }

func sortPairs(p []Pair, sortByA, prioritySmallestKey1, prioritySmallestKey2 bool) {
	f := []func(int, int) bool{func(a, b int) bool { return a < b }, func(a, b int) bool { return a > b }}
	f1 := cond(prioritySmallestKey1, 0, 1)
	f2 := cond(prioritySmallestKey2, 0, 1)
	if sortByA == true {
		sort.Slice(p, func(i, j int) bool { return cond(p[i].a == p[j].a, f[f2](p[i].b, p[j].b), f[f1](p[i].a, p[j].a)) })
	} else {
		sort.Slice(p, func(i, j int) bool { return cond(p[i].b == p[j].b, f[f2](p[i].a, p[j].a), f[f1](p[i].b, p[j].b)) })
	}
}
func pairs2map(p []Pair) map[Pair]int {
	ret := make(map[Pair]int)
	for i := 0; i < len(p); i++ {
		ret[p[i]]++
	}
	return ret
}
func map2pair(m map[int]int) []Pair {
	t := make([]Pair, 0, len(m))
	for i, v := range m {
		t = append(t, Pair{i, v})
	}
	return t
}
func splitPair(p []Pair) ([]int, []int) {
	res := make([]int, len(p))
	res2 := make([]int, len(p))
	for i, v := range p {
		res[i] = v.a
		res2[i] = v.b
	}
	return res, res2
}
func slice2Pairs(a, b []int) []Pair {
	if len(a) != len(b) {
		return nil
	}
	ret := make([]Pair, 0, len(a))
	for i := 0; i < len(a); i++ {
		ret = append(ret, Pair{a[i], b[i]})
	}
	return ret
}

// 文字列
// 左と右から文字が出現する位置を返す
func findChar(s string, p byte) ([]int, []int) {
	ret := make([]int, 0)
	ret2 := make([]int, 0)
	for i := 0; i < len(s); i++ {
		if s[i] == p {
			ret = append(ret, i)
			ret2 = append(ret2, len(s)-i-1)
		}
	}
	return ret, ret2
}
func repeat(s string, n int) string {
	return strings.Repeat(s, n)
}

// グラフ
type Graph struct {
	n     int
	edges [][]Edge
}
type Edge struct {
	from, to, w int
}

func NewGraph(n int) *Graph {
	g := &Graph{}
	g.n = n
	g.edges = make([][]Edge, g.n)
	return g
}
func (g *Graph) AddEdge(a, b, c int) {
	var t Edge
	t.from, t.to, t.w = a, b, c
	g.edges[a] = append(g.edges[a], t)
}
func (g *Graph) ReadSimpleUndirectedGraph(m int) {
	for i := 0; i < m; i++ {
		a, b := ri2()
		g.AddEdge(a, b, 1)
		g.AddEdge(b, a, 1)
	}
}
func (g *Graph) ReadWightedUndirectedGraph(m int) {
	for i := 0; i < m; i++ {
		a, b, c := ri3()
		g.AddEdge(a, b, c)
		g.AddEdge(b, a, c)
	}
}
func (g *Graph) ReadSimpleDirectedGraph(m int) {
	for i := 0; i < m; i++ {
		a, b := ri2()
		g.AddEdge(a, b, 1)
	}
}
func (g *Graph) ReadWightedDirectedGraph(m int) {
	for i := 0; i < m; i++ {
		a, b, c := ri3()
		g.AddEdge(a, b, c)
	}
}
func (g *Graph) PairToEdge(p []Pair, undirected bool) {
	for i := 0; i < len(p); i++ {
		g.AddEdge(p[i].a, p[i].b, 1)
		if undirected == true {
			g.AddEdge(p[i].b, p[i].a, 1)
		}
	}
}
func (g *Graph) SortEdgeByNode(prioritySmallest bool) {
	for v := 0; v < len(g.edges); v++ {
		if prioritySmallest == true {
			sort.Slice(g.edges[v], func(i, j int) bool {
				return g.edges[v][i].to < g.edges[v][j].to
			})
		} else {
			sort.Slice(g.edges[v], func(i, j int) bool {
				return g.edges[v][i].to > g.edges[v][j].to
			})
		}
	}
}
func readMatrixEdges(n, m int, readCost, directed bool) [][]int {
	ret := intSlice2(n, n, 0)
	a, b, c := 0, 0, 1
	for i := 0; i < m; i++ {
		if readCost == true {
			a, b, c = ri3()
		} else {
			a, b = ri2()
		}
		ret[a][b] = c
		if directed == false {
			ret[b][a] = c
		}
	}
	return ret
} // 隣接行列の読み込み
func restorePath(p []int, begin, end int) []int {
	ret := make([]int, 0)
	cur := end
	ret = append(ret, cur)
	for cur != -1 && cur != begin {
		ret = append(ret, p[cur])
		cur = p[cur]
	}
	ret = reverseList(ret)
	return ret
} // 最短パス復元(BFS,ダイクストラ,ベルマンフォード共通)
func searchGrid(g [][]byte, s string) [][]Pair {
	ret := make([][]Pair, len(s))
	for i := 0; i < len(g); i++ {
		for j := 0; j < len(g[0]); j++ {
			for k := 0; k < len(s); k++ {
				if g[i][j] == s[k] {
					ret[k] = append(ret[k], Pair{i, j})
				}
			}
		}
	}
	return ret
} //Grid上の対象の座標を探索

// BIT
type FenwickTree struct {
	data []int
	len  int
}

func NewFenwickTree(n int) *FenwickTree {
	ret := &FenwickTree{}
	ret.data = make([]int, n)
	ret.len = n
	return ret
}
func (f *FenwickTree) Add(p, x int) {
	if p < 0 || p >= f.len {
		panic("worong range")
	}
	p += 1
	for p <= f.len {
		f.data[p-1] += x
		p += p & -p
	}
}
func (f *FenwickTree) Replace(p, x int) {
	if p < 0 || p >= f.len {
		panic("wrong range")
	}
	oldValue := f.Sum(p, p+1)
	diff := x - oldValue
	f.Add(p, diff)
}

// Sum 区間[l,r)の合計
func (f *FenwickTree) Sum(l, r int) int {
	if l < 0 || l >= f.len || r < 0 || r > f.len || l > r {
		return 0
	}
	sum := func(r int) int {
		s := 0
		for r > 0 {
			s += f.data[r-1]
			r -= r & -r
		}
		return s
	}
	return sum(r) - sum(l)
}

// ModSum 区間[l,r)の合計(MOD)
func (f *FenwickTree) ModSum(l, r, mod int) int {
	if l < 0 || l >= f.len || r < 0 || r > f.len || l > r {
		return 0
	}
	sum := func(r int) int {
		s := 0
		for r > 0 {
			s += f.data[r-1]
			s %= mod
			r -= r & -r
		}
		return s % mod
	}
	return (sum(r) - sum(l) + mod) % mod
}
func (f *FenwickTree) Set(l []int) {
	n := len(l)
	if n != f.len {
		panic("worong length")
	}
	for i, v := range l {
		f.Add(i, v)
	}
}
func (f *FenwickTree) LowerBound(l, k int) (int, int, bool) {
	if f.Sum(l, f.len) < k {
		return f.len, 0, false
	}
	b := f.Sum(0, l) // l までの累積和を取得
	idx := sort.Search(f.len, func(i int) bool {
		return f.Sum(0, i) >= b+k // l を考慮した累積和
	})
	return idx, f.Sum(l, idx), true
}
func (f *FenwickTree) RangeCount(idx, nmax int) int {
	ret1, _, ok := f.LowerBound(idx, nmax+1)
	ret2, _, _ := f.LowerBound(idx, 0)
	if ok == true {
		return ret1 - ret2 - 1
	} else {
		return ret1 - ret2
	}
}

// 座圧して転倒数を求める
func countNumberOfFall(a []int) int {
	ret := 0
	t, _, _ := compressCoordinate(a)
	f := NewFenwickTree(len(t))
	for i := len(t) - 1; i >= 0; i-- {
		f.Add(t[i], 1)
		ret += f.Sum(0, t[i])
	}
	return ret
}

// [l,r)についてvalを区間加算、[l,r)の区間和を返すクロージャーを返す
func rangeBIT(n int) (func(int, int, int), func(int, int) int) {
	f0 := NewFenwickTree(n + 1)
	f1 := NewFenwickTree(n + 1)
	rangeAddFn := func(l, r, val int) {
		f0.Add(l, -val*l)
		f0.Add(r, val*r)
		f1.Add(l, val)
		f1.Add(r, -val)
	}
	sumFn := func(l, r int) int {
		ret := f0.Sum(0, r) + f1.Sum(0, r)*r - f0.Sum(0, l) + f1.Sum(0, l)*l
		return ret
	}
	return rangeAddFn, sumFn
}

// セグメント木
type SegTree[T any] struct {
	data []T
	e    T
	op   func(T, T) T
	len  int
}

// NewSegInt セグメント木(int)の生成ラッパー(Min,Max,Sum)に対応
func NewSegInt(n int, qt string) *SegTree[int] {
	if qt == "Min" {
		return NewSegTree[int](n, 1<<61, func(a, b int) int {
			if a < b {
				return a
			} else {
				return b
			}
		})
	} else if qt == "Max" {
		return NewSegTree[int](n, 0, func(a, b int) int {
			if a > b {
				return a
			} else {
				return b
			}
		})
	} else if qt == "Sum" {
		return NewSegTree[int](n, 0, func(a, b int) int {
			return a + b
		})
	}
	return nil
}

func NewSegTree[T any](n int, e T, op func(T, T) T) *SegTree[T] {
	ret := &SegTree[T]{}
	ret.e = e
	ret.op = op
	ret.len = 1
	for ret.len < n {
		ret.len *= 2
	}
	ret.data = make([]T, ret.len*2-1)
	for i := 0; i < ret.len; i++ {
		ret.data[i] = ret.e
	}
	return ret
}
func (seg *SegTree[T]) SetSlice(vals []T) {
	for i := 0; i < len(vals); i++ {
		seg.data[i] = vals[i]
	}
	for i := 0; i < seg.len*2-2; i += 2 {
		seg.data[i/2+seg.len] = seg.op(seg.data[i], seg.data[i+1])
	}

}

func (seg *SegTree[T]) Update(idx int, val T) {
	cur := idx
	seg.data[cur] = val
	for cur < seg.len*2-2 {
		if cur%2 == 1 {
			seg.data[cur/2+seg.len] = seg.op(seg.data[cur-1], seg.data[cur])
		} else {
			seg.data[cur/2+seg.len] = seg.op(seg.data[cur], seg.data[cur+1])
		}
		cur = cur/2 + seg.len
	}
}

// 半開区間[l,r)のクエリ
func (seg *SegTree[T]) Query(l, r int) T {
	ret := seg.e
	for l < r {
		if l%2 == 1 {
			ret = seg.op(ret, seg.data[l])
			l++
		}
		if r%2 == 1 {
			ret = seg.op(ret, seg.data[r-1])
			r--
		}
		if l == r {
			return ret
		}
		l = l/2 + seg.len
		r = r/2 + seg.len
	}
	ret = seg.op(ret, seg.data[l])
	return ret
}

// スライスの[l,r)について昇順(or 降順)の場合にtrueとなるクロージャーを返す
func sliceOrderChecker(a []int, asc bool) (func(int, int), func(int, int) bool) {
	dat := make([]int, len(a))
	copy(dat, a)
	var fn func(int, int) int
	if asc == true {
		fn = func(u, v int) int { return cond(u <= v, 1, 0) }
	} else {
		fn = func(u, v int) int { return cond(u >= v, 1, 0) }
	}
	d := make([]int, len(a))
	d[len(a)-1] = 1
	for i := 0; i < len(a)-1; i++ {
		d[i] = fn(a[i], a[i+1])
	}
	seg := NewSegTree[int](len(d), 1, func(u, v int) int { return cond(u == 1 && v == 1, 1, 0) })
	seg.SetSlice(d)
	update := func(idx, val int) {
		dat[idx] = val
		if len(dat) == 1 {
			return
		}
		if idx != len(dat)-1 {
			seg.Update(idx, fn(dat[idx], dat[idx+1]))
		}
		if idx != 0 {
			seg.Update(idx-1, fn(dat[idx-1], dat[idx]))
		}
	}
	query := func(l, r int) bool {
		if r-l == 0 || seg.Query(l, r-1) == 1 {
			return true
		}
		return false
	}
	return update, query
}

// 区間[l,r)に含まれる文字カウント、辞書順の最小文字、最大文字、全体の文字カウントを求めるクロージャーを返す
func charSet(a []int) (func(int, int), func(int, int) ([]int, int, int, []int)) {
	const maxCharTypes = 26
	dat := make([]int, len(a))
	copy(dat, a)
	count := intSlice(maxCharTypes, 0)
	seg := make([]*SegTree[int], maxCharTypes)
	for i := 0; i < maxCharTypes; i++ {
		seg[i] = NewSegInt(len(a), "Sum")
	}
	for i := 0; i < len(a); i++ {
		idx := a[i]
		seg[idx].Update(i, 1)
		count[idx]++
	}
	update := func(idx, val int) {
		old := dat[idx]
		next := val
		dat[idx] = next
		seg[old].Update(idx, 0)
		seg[next].Update(idx, 1)
		count[old]--
		count[next]++
	}
	query := func(l, r int) ([]int, int, int, []int) {
		ret := intSlice(maxCharTypes, 0)
		minIdx, maxIdx := -1, -1
		for i := 0; i < maxCharTypes; i++ {
			t := seg[i].Query(l, r)
			if minIdx == -1 && t != 0 {
				minIdx = i
			}
			if t != 0 {
				maxIdx = i
			}
			ret[i] += t
		}
		return ret, minIdx, maxIdx, count
	}
	return update, query
}

// DualSeg 双対セグメント木(区間更新(or 区間加算)、点取得)
type DualSeg[T any] struct {
	lazy         []T
	e            T
	n            int
	op           func(T, T) T
	curUpdateCnt int
	updateCnt    []int
	ranges       [][2]int
}

// NewDualSegInt 双対セグメント木のInt用の初期化ラッパー関数
func NewDualSegInt(d []int, isRangeReplacement bool) *DualSeg[int] {
	if isRangeReplacement {
		seg := NewDualSeg[int](len(d), 0, nil)
		seg.SetSlice(d)
		return seg
	} else {
		seg := NewDualSeg[int](len(d), 0, func(a, b int) int { return a + b })
		seg.SetSlice(d)
		return seg
	}
}

// NewDualSeg 汎用双対セグメント木(opがnilの場合は、区間更新)
func NewDualSeg[T any](n int, e T, op func(T, T) T) *DualSeg[T] {
	t := 1
	for t < n {
		t *= 2
	}
	n = t
	data := make([]T, 2*n-1)
	updateCnt := make([]int, 2*n-1)
	ranges := make([][2]int, 2*n-1)

	for i := 0; i < n*2-1; i++ {
		if i < n {
			ranges[i] = [2]int{i, i + 1}
			continue
		}
		ranges[i] = [2]int{ranges[(i-n)*2][0], ranges[(i-n)*2+1][1]}
	}
	return &DualSeg[T]{
		lazy:         data,
		n:            n,
		e:            e,
		op:           op,
		ranges:       ranges,
		curUpdateCnt: 1,
		updateCnt:    updateCnt,
	}

}
func (dst *DualSeg[T]) SetSlice(d []T) {
	for i := 0; i < len(d); i++ {
		dst.lazy[i] = d[i]
	}
}

// Update [l,r)の区間作用
func (dst *DualSeg[T]) Update(l, r int, val T) {
	dst.curUpdateCnt++
	if r-l == 1 {
		if dst.op == nil {
			dst.lazy[l] = val
			dst.updateCnt[l] = dst.curUpdateCnt
		} else {
			dst.lazy[l] = dst.op(val, dst.lazy[l])
		}
		return
	}
	dst.update(dst.n*2-2, l, r, val)

}
func (dst *DualSeg[T]) update(idx, l, r int, val T) {
	if l >= r {
		return
	}
	if l <= dst.ranges[idx][0] && dst.ranges[idx][1] <= r {
		if dst.op == nil {
			dst.lazy[idx] = val
			dst.updateCnt[idx] = dst.curUpdateCnt
		} else {
			dst.lazy[idx] = dst.op(dst.lazy[idx], val)
		}
		return
	}
	ni := (idx - dst.n) * 2
	nl := dst.ranges[ni]
	nr := dst.ranges[ni+1]
	if nl[0] <= l && l < nl[1] {
		if nl[1] < r {
			dst.update(ni, l, nl[1], val)
		} else {
			dst.update(ni, l, r, val)
		}
	}
	if r <= nr[1] && nr[0] <= r {
		if nr[0] > l {
			dst.update(ni+1, nr[0], r, val)
		} else {
			dst.update(ni+1, l, r, val)
		}
	}
}

func (dst *DualSeg[T]) Get(index int) T {
	ret := dst.lazy[index]
	cur := dst.updateCnt[index]
	for index < 2*dst.n-2 {
		index = index/2 + dst.n
		if dst.op == nil {
			if cur < dst.updateCnt[index] {
				cur = dst.updateCnt[index]
				ret = dst.lazy[index]
			}
		} else {
			ret = dst.op(ret, dst.lazy[index])
		}
	}
	return ret
}

// UnionFind
type UnionFind struct {
	root  []int
	size  []int
	group int
}

func NewUnionFind(n int) *UnionFind {
	root := make([]int, n)
	size := make([]int, n)
	for i := 0; i < n; i++ {
		root[i] = i
		size[i] = 1
	}
	uf := &UnionFind{root: root, size: size, group: n}
	return uf
}
func (uf *UnionFind) Union(p int, q int) {
	qRoot := uf.Root(q)
	pRoot := uf.Root(p)
	if qRoot == pRoot {
		return
	}
	uf.group--
	if uf.size[qRoot] < uf.size[pRoot] {
		uf.root[qRoot] = uf.root[pRoot]
		uf.size[pRoot] += uf.size[qRoot]
	} else {
		uf.root[pRoot] = uf.root[qRoot]
		uf.size[qRoot] += uf.size[pRoot]
	}
}
func (uf *UnionFind) Root(p int) int {
	if p > len(uf.root)-1 {
		return -1
	}
	for uf.root[p] != p {
		uf.root[p] = uf.root[uf.root[p]]
		p = uf.root[p]
	}
	return p
}
func (uf *UnionFind) find(p int) int {
	return uf.Root(p)
}
func (uf *UnionFind) Connected(p int, q int) bool {
	return uf.Root(p) == uf.Root(q)
}
func (uf *UnionFind) Groups() map[int]int {
	cm := make(map[int]int)
	for i := 0; i < len(uf.root); i++ {
		t := uf.find(uf.root[i])
		cm[t]++
	}
	return cm
}

// Deque
type List[T comparable] struct {
	first                *element[T]
	last                 *element[T]
	size                 int
	pos                  map[T]*element[T]
	recordLastElementPos bool
}

// element リスト内の各要素
type element[T comparable] struct {
	value T
	prev  *element[T]
	next  *element[T]
}

// NewDeque 新しい双方向リンクリストを生成する。recordLastElementPosがtrueの場合、要素の追加位置を記録する。
func NewDeque[T comparable](recordLastElementPos bool) *List[T] {
	t := List[T]{}
	if recordLastElementPos {
		t.pos = make(map[T]*element[T])
		t.recordLastElementPos = true
	}
	return &t
}

// PushBack リストの末尾に新しい要素を追加する
func (l *List[T]) PushBack(a T) {
	if l.size == 0 {
		l.size++
		e := &element[T]{value: a}
		l.first = e
		l.last = e
		if l.recordLastElementPos {
			l.pos[a] = e
		}
		return
	}
	l.size++
	curLast := l.last
	nextLast := element[T]{value: a, prev: curLast}
	curLast.next = &nextLast
	l.last = &nextLast
	if l.recordLastElementPos {
		l.pos[a] = &nextLast
	}
}

// PushFront リストの先頭に新しい要素を追加する
func (l *List[T]) PushFront(a T) {
	if l.size == 0 {
		l.size++
		e := &element[T]{value: a}
		l.first = e
		l.last = e
		if l.recordLastElementPos {
			l.pos[a] = e
		}
		return
	}
	l.size++
	curHead := l.first
	nextHead := element[T]{value: a, next: curHead}
	curHead.prev = &nextHead
	l.first = &nextHead
	if l.recordLastElementPos {
		l.pos[a] = &nextHead
	}
}

// Front リストの最初の要素の値を返す
func (l *List[T]) Front() T {
	return l.first.value
}

// Back リストの最後の要素の値を返す
func (l *List[T]) Back() T {
	return l.last.value
}

// PopFront リストの最初の要素を削除し、その値を返す
func (l *List[T]) PopFront() T {
	if l.size == 0 {
		panic("PopFront(): index error(size=0)")
	}
	if l.recordLastElementPos {
		panic("PopFront():　can't be used with recordLastElementPos option")
	}
	l.size--
	ret := l.first.value
	l.first = l.first.next
	if l.first != nil { // リストが空になった場合を考慮
		l.first.prev = nil
	}

	return ret
}

// PopBack リストの最後の要素を削除し、その値を返す
func (l *List[T]) PopBack() T {
	if l.size == 0 {
		panic("PopBack(): index error(size=0)")
	}
	if l.recordLastElementPos {
		panic("PopBack():　can't be used with recordLastElementPos option")
	}
	l.size--
	ret := l.last.value
	l.last = l.last.prev
	if l.last != nil { // リストが空になった場合を考慮
		l.last.next = nil
	}
	return ret
}

// Len リストの長さ（要素数）を返す
func (l *List[T]) Len() int {
	return l.size
}

// DumpFront リストの要素を先頭から順に配列として返す
func (l *List[T]) DumpFront() []T {
	cur := l.first
	ret := make([]T, 0)
	for cur != nil {
		ret = append(ret, cur.value)
		cur = cur.next
	}
	return ret
}

// DumpBack リストの要素を末尾から順に配列として返す
func (l *List[T]) DumpBack() []T {
	cur := l.last
	ret := make([]T, 0)
	for cur != nil {
		ret = append(ret, cur.value)
		cur = cur.prev
	}
	return ret
}

// remove　指定された要素をリストから削除する
func (l *List[T]) Remove(v T) {
	e, ok := l.pos[v]
	if !ok {
		return
	}
	l.size--
	if e.next == nil {
		l.last = e.prev
		if l.last != nil { // リストが空になった場合を考慮
			l.last.next = nil
		}
	} else if e.prev == nil {
		l.first = e.next
		if l.first != nil { // リストが空になった場合を考慮
			l.first.prev = nil
		}
	} else {
		e.prev.next = e.next
		e.next.prev = e.prev
	}
}

// insertAfter 指定された要素の後に新しい要素を挿入する
func (l *List[T]) InsertAfter(v, k T) {
	e, ok := l.pos[v]
	if !ok {
		return
	}
	ie := &element[T]{value: k}
	ie.next = e.next
	ie.prev = e
	if e.next != nil {
		e.next.prev = ie
	}
	e.next = ie
	if l.recordLastElementPos {
		l.pos[k] = ie
	}
	l.size++
}

// insertBefore 指定された要素の前に新しい要素を挿入する
func (l *List[T]) InsertBefore(v, k T) {
	e, ok := l.pos[v]
	if !ok {
		return
	}
	ie := &element[T]{value: k}
	ie.prev = e.prev
	ie.next = e
	if e.prev != nil {
		e.prev.next = ie
	} else {
		l.first = ie
	}
	e.prev = ie
	if l.recordLastElementPos {
		l.pos[k] = ie
	}
	l.size++
}

// ヒープ
type PQ[T comparable] struct {
	d                []T
	prioritySmallest bool
	lessFunc         func(a, b T) bool
}

// NewPQ PQの初期化関数
func NewPQ[T constraints.Ordered](prioritySmallest bool) *PQ[T] {
	f := func(a, b T) bool {
		if a < b {
			return true
		} else {
			return false
		}
	}
	return NewPQWithLessFunc[T](prioritySmallest, f)
}
func orderedLessFunc[T constraints.Ordered](a, b T) bool {
	if a < b {
		return true
	}
	return false
}

// NewPairPQ
func NewPairPQ(isKeyA bool, prioritySmallest bool) *PQ[Pair] {
	f := func(a, b Pair) bool {
		if isKeyA {
			if a.a < b.a {
				return true
			}
			return false
		} else {
			if a.b < b.b {
				return true
			}
			return false
		}
	}
	return NewPQWithLessFunc[Pair](prioritySmallest, f)
}

// NewIntPQ 過去ライブラリからの呼び出し用
func NewIntPQ(prioritySmallest bool) *PQ[int] {
	f := func(a, b int) bool {
		if a < b {
			return true
		}
		return false
	}
	return NewPQWithLessFunc[int](prioritySmallest, f)
}

// NewItemPQ 過去ライブラリからの呼び出し用
type Item struct{ key, num int }

func NewItemPQ(prioritySmallest bool) *PQ[Item] {
	less := func(a, b Item) bool {
		if a.key < b.key {
			return true
		}
		return false
	}
	return NewPQWithLessFunc[Item](prioritySmallest, less)
}

// NewPQWithLessFunc 汎用PQ初期化関数
func NewPQWithLessFunc[T comparable](prioritySmallest bool, lessFunc func(T, T) bool) *PQ[T] {
	ret := &PQ[T]{}
	ret.d = make([]T, 0, 100)
	n := ret.Len()
	for i := n/2 - 1; i >= 0; i-- {
		ret.down(i, n)
	}
	ret.prioritySmallest = prioritySmallest
	ret.lessFunc = lessFunc
	return ret
}
func (pq *PQ[T]) less(i, j int) bool {
	if pq.prioritySmallest == true {
		return pq.lessFunc(pq.d[i], pq.d[j])
	} else {
		return !pq.lessFunc(pq.d[i], pq.d[j])
	}
}
func (pq *PQ[T]) swap(i, j int) { pq.d[i], pq.d[j] = pq.d[j], pq.d[i] }
func (pq *PQ[T]) down(i0, n int) bool {
	i := i0
	for {
		j1 := 2*i + 1
		if j1 >= n || j1 < 0 { // j1 < 0 after int overflow
			break
		}
		j := j1 // left child
		if j2 := j1 + 1; j2 < n && pq.less(j2, j1) {
			j = j2 // = 2*i + 2  // right child
		}
		if !pq.less(j, i) {
			break
		}
		pq.swap(i, j)
		i = j
	}
	return i > i0
}
func (pq *PQ[T]) up(j int) {
	for {
		i := (j - 1) / 2 // parent
		if i == j || !pq.less(j, i) {
			break
		}
		pq.swap(i, j)
		j = i
	}
}
func (pq *PQ[T]) Push(x T) {
	pq.d = append(pq.d, x)
	pq.up(len(pq.d) - 1)
}
func (pq *PQ[T]) Pop() T {
	n := pq.Len() - 1
	x := pq.d[0]
	pq.swap(0, n)
	pq.down(0, n)
	pq.d = pq.d[0 : pq.Len()-1]
	return x
}
func (pq *PQ[T]) Len() int {
	return len(pq.d)
}
func (pq *PQ[T]) Peek() T {
	return pq.d[0]
}
func (pq *PQ[T]) PushSlice(a []T) {
	for _, v := range a {
		pq.Push(v)
	}
}
func (pq *PQ[T]) Remove(i int) T {
	n := pq.Len() - 1
	if n != i {
		pq.swap(i, n)
		if !pq.down(i, n) {
			pq.up(i)
		}
	}
	return pq.Pop()
}
func (pq *PQ[T]) Fix(i int) {
	if !pq.down(i, pq.Len()) {
		pq.up(i)
	}
}
func (pq *PQ[T]) PopAndPush(x T) T {
	ret := pq.Peek()
	pq.d[0] = x
	pq.down(0, pq.Len())
	return ret
}
func (pq *PQ[T]) PopUniq() T {
	ret := pq.Pop()
	for pq.Len() != 0 && pq.Peek() == ret {
		pq.Pop()
	}
	return ret
}

// 整数関連
// 最小公倍数の計算
func lcm(a, b int) int {
	return (a / gcd(a, b)) * b
}

// 最大公約数の計算
func gcd(a, b int) int {
	if b == 0 {
		return a
	}
	c := 1
	for c != 0 {
		c = a % b
		a, b = b, c
	}
	return a
}

// 拡張ユークリッド互除法(aX+bY=1)となるX,Yを求める
func exgcd(a, b int) (int, int) {
	q := 0
	x0, x1, y0, y1 := 1, 0, 0, 1
	for b != 0 {
		q, a, b = a/b, b, a%b
		x0, x1 = x1, x0-q*x1
		y0, y1 = y1, y0-q*y1
	}
	return x0, y0
}
func divisorList(n int) []int {
	var l []int
	for i := 1; i*i <= n; i++ {
		if n%i == 0 {
			l = append(l, i)
			if i != n/i {
				l = append(l, n/i)
			}
		}
	}
	sort.Slice(l, func(i, j int) bool { return l[i] < l[j] })
	return l
}
func divisorCnt(maxNum int) func(int) int {
	memo := intSlice(maxNum, -1)
	f := func(n int) int {
		if memo[n] != -1 {
			return memo[n]
		}
		var cnt int
		for i := 1; i*i <= n; i++ {
			if n%i == 0 {
				cnt++
				if i != n/i {
					cnt++
				}
			}
		}
		memo[n] = cnt
		return cnt
	}
	return f
}
func divisorPairs(n int) []Pair {
	var p []Pair
	for i := 1; i*i <= n; i++ {
		if n%i == 0 {
			p = append(p, Pair{i, n / i})
		}
	}
	return p
}
func factorization(n int) map[int]int {
	m := make(map[int]int)
	for i := 2; i*i <= n; i++ {
		for n%i == 0 {
			m[i]++
			n = n / i
		}
	}
	if n != 0 && n != 1 {
		m[n]++
	}
	return m
}
func fastFactorization(n int) func(x int) []Pair {
	rp := make([]int, n+1)
	p := primeList(n)
	rp[1] = 1
	for _, v := range p {
		for i := v; i <= n; i += v {
			if rp[i] == 0 {
				rp[i] = v
			}
		}
	}
	rp[1] = 1
	// k を素因数分解して []Pair{素因数, 指数} を返す内部関数
	var factorFunc func(k int) []Pair
	factorFunc = func(k int) []Pair {
		res := make([]Pair, 0)
		for k > 1 {
			sp := rp[k] // kの最小素因数を取得
			cnt := 0
			for k > 1 && rp[k] == sp {
				k /= sp
				cnt++
			}
			res = append(res, Pair{a: sp, b: cnt})
		}
		return res
	}
	return factorFunc
}
func isPrime(n int) bool { return big.NewInt(int64(n)).ProbablyPrime(0) }
func primeList(n int) []int {
	if n < 2 {
		return nil
	}
	l := make([]bool, n+1)
	l[0], l[1] = true, true

	for i := 2; i*i <= n; i++ {
		if !l[i] {
			for j := i * i; j <= n; j += i {
				l[j] = true
			}
		}
	}
	primes := make([]int, 0, n/2)
	for i := 2; i <= n; i++ {
		if !l[i] {
			primes = append(primes, i)
		}
	}
	return primes
}
func powMod(x, k, m int) int {
	if k == 0 {
		return 1
	}
	if x > m {
		x %= m
	}
	if k%2 == 0 {
		return powMod(x*x%m, k/2, m)
	} else {
		return x * powMod(x, k-1, m) % m
	}
}
func pow(a, b int) int {
	res := 1
	for b > 0 {
		if b&1 == 1 {
			res = res * a
		}
		a = a * a
		b >>= 1
	}
	return res
}
func combination(n, r int) int {
	if n < r {
		return 0
	}
	r = min(n-r, r)
	d := make([]int, r)

	for i := 0; i < r; i++ {
		d[i] = n - i
	}
	for i := 2; i <= r; i++ {
		ti := i
		for j := 0; j < r; j++ {
			g := gcd(d[j], ti)
			if g != 1 {
				ti /= g
				d[j] /= g
			}
			if ti == 1 {
				break
			}
		}
	}
	ret := 1
	for i := 0; i < r; i++ {
		ret *= d[i]
	}
	return ret
}
func combinationMod(a, b int) int {
	t1, t2 := 1, 1
	for i := 2; i <= b; i++ {
		t2 = (i * t2) % MOD
	}
	inv := modInv(t2)
	for i := a - b + 1; i <= a; i++ {
		t1 = (i * t1) % MOD
	}
	return (t1 * inv) % MOD
}

// cnt個をgroup(1グループminCnt以上)に分割する組み合わせ
func combinationGroupMod(cnt, group, minCnt int) int {
	return combinationMod((cnt-group*minCnt)+group-1, group-1)
}

func sqrt(x int) int                  { return int(math.Sqrt(float64(x))) }
func cbrt(x int) int                  { return int(math.Cbrt(float64(x))) }
func seqSum(x int) int                { return (x*x + x) / 2 }
func seqRangeSum(from, to int) int    { return seqSum(to) - seqSum(from-1) }
func seqSumMod(x int) int             { return modMul(modAdd(modMul(x%MOD, x%MOD), x%MOD), modInv(2)) }
func seqRangeSumMod(from, to int) int { return modSub(seqSum(to), seqSum(from-1)) }

// 等差数列(初項a,公差d)について、y[0,maxY],x[0,maxX]の条件でxの範囲を求める
func getArithmeticSeqRange(d, a, maxY, maxX int) (int, int) {
	t := (-a + d - 1) / d
	return max(1, t), min(maxX, (maxY-a)/d)
}

// n項までの等比数列の和(mod更新）
func sumOfGeometricSequence(a, r, n int) int {
	rn := powMod(r, n, MOD)
	inv := modInv(r - 1)
	return modMul(modSub(rn, a), inv)
}
func MulMatrix(m1, m2 [][]int, mod int) [][]int {
	size := len(m1)
	ret := make([][]int, size)
	for i := 0; i < size; i++ {
		ret[i] = make([]int, size)
	}
	for i := 0; i < size; i++ {
		for j := 0; j < size; j++ {
			for k := 0; k < size; k++ {
				ret[i][k] += m1[i][j] * m2[j][k]
				ret[i][k] %= mod
			}
		}
	}
	return ret
} // 正方行列の掛け算
func PowMatrix(m [][]int, n int, mod int) [][]int {
	// 行列累乗
	// a_0=s a_1=t
	// a_(i+2) = p*a_(i+1) + q*a_i
	//           ↓
	// |a_(i+2)| = | p q |^n (a_1)
	// |a_(i+1)| = | 1 0 |   (a_0)
	size := len(m)
	tm := make([][]int, size)
	for i := 0; i < size; i++ {
		tm[i] = make([]int, size)
		tm[i][i] = 1
	}
	for n >= 2 {
		if n%2 == 0 {
			m = MulMatrix(m, m, mod)
			n = n / 2
		} else {
			tm = MulMatrix(tm, m, mod)
			m = MulMatrix(m, m, mod)
			n = (n - 1) / 2
		}
	}
	m = MulMatrix(tm, m, mod)
	return m
} // 正方行列の冪乗

// int型操作(1-indexed)
func getDigitLen(x int) int {
	if x == 0 {
		return 1
	}
	d := 0
	for x > 0 {
		d++
		x /= 10
	}
	return d
}
func getDigit(x, idx int) int { return cond(idx > 17 || idx < 1, 0, (x/p10[idx-1])%10) }
func setDigit(x, idx, v int) int {
	return cond(idx > 17 || v > 9 || v < 0, 0, x+(v-getDigit(x, idx))*p10[idx-1])
}
func swapDigit(x, idx1, idx2 int) int {
	t1 := getDigit(x, idx1)
	t2 := getDigit(x, idx2)
	x = setDigit(x, idx2, t1)
	x = setDigit(x, idx1, t2)
	return x
}
func getTopDigit(x int) int { return getDigit(x, getDigitLen(x)) }

// ビット操作(0-indexed)
func bitLen[T constraints.Integer](x T) int { return bits.Len(uint(x)) }                                     // xの2進数での長さを取得する
func getNthBit(x, idx int) int              { return cond(x&(1<<uint(idx)) == 0, 0, 1) }                     // idx番目のbitを取得する
func setNthBit(x, idx, bit int) int         { return cond(bit == 0, x & ^(1<<uint(idx)), x|(1<<uint(idx))) } // idx番目のbitを変更する
func toggleNthBit(x, idx int) int           { return x ^ (1 << uint(idx)) }                                  // idx番目のbitを反転させる
func itobstr(x, digits int) string          { return fmt.Sprintf("%0*b", digits, x) }                        // 数値をバイナリ表記したstringに変換する(デバッグ用)
func btoi(b []byte) int {
	ret, _ := strconv.ParseInt(string(b), 2, 64)
	return int(ret)
}                                // バイナリ表記[]byteをintに変換する
func bitRightmostOne(n int) int  { return bits.TrailingZeros(uint(n)) }  // bitが1になっている一番右側の位置を返す
func bitRightmostZero(n int) int { return bits.TrailingZeros(^uint(n)) } // bitが0になっている一番右側の位置を返す
func getBitPosConv(mask int) []int {
	t := make([]int, bits.OnesCount(uint(mask)))
	k := bits.Len(uint(mask))
	cnt := 0
	for i := 0; i < k; i++ {
		if getNthBit(mask, i) == 1 {
			t[cnt] = i
			cnt++
		}
	}
	return t
} // bitが1になっている位置の一覧を返す

// Pair操作
func subPair(p, t Pair) Pair     { return Pair{p.a - t.a, p.b - t.b} }
func addPair(p, t Pair) Pair     { return Pair{p.a + t.a, p.b + t.b} }
func mulPair(p Pair, d int) Pair { return Pair{p.a * d, p.b * d} }
func detPair(p, t Pair) int      { return p.a*t.b - p.b*t.a }
func dotPair(p, t Pair) int      { return p.a*t.a + p.b*t.b }
func distPair(p, t Pair) int     { return dotPair(subPair(p, t), subPair(p, t)) }
func distIntMatrix(p []Pair) [][]int {
	n := len(p)
	ret := intSlice2(n, n, INF)
	for i := 0; i < n-1; i++ {
		for j := i + 1; j < n; j++ {
			t := distPair(p[i], p[j])
			ret[i][j] = t
			ret[j][i] = t
		}
	}
	return ret
}

// []Pairの各点間の距離を求める
func distFloatMatrix(p []Pair) [][]float64 {
	n := len(p)
	ret := make([][]float64, n)
	for i := 0; i < n; i++ {
		ret[i] = make([]float64, n)
		for j := 0; j < n; j++ {
			ret[i][j] = math.MaxFloat32
		}
	}
	for i := 0; i < n-1; i++ {
		for j := i + 1; j < n; j++ {
			t := math.Sqrt(float64(distPair(p[i], p[j])))
			ret[i][j] = t
			ret[j][i] = t
		}
	}
	return ret
}
func intersectSum(p1, p2 Pair) int {
	return max(0, min(p1.b, p2.b)-max(p1.a, p2.a))
} // [a1,b1),[a2,b2)の重複区間のカウント
func normalizePairs(p []Pair) []Pair {
	ma, mb := INF, INF
	for i := 0; i < len(p); i++ {
		ma = min(ma, p[i].a)
		mb = min(mb, p[i].b)
	}
	ret := make([]Pair, len(p))
	for i := 0; i < len(p); i++ {
		ret[i].a = p[i].a - ma
		ret[i].b = p[i].b - mb
	}
	return ret
}
func addPairs(p []Pair, d Pair) []Pair {
	ret := make([]Pair, len(p))
	for i := 0; i < len(p); i++ {
		ret[i] = addPair(p[i], d)
	}
	return ret
}
func sumProductOfPairs(p []Pair) int {
	ret := 0
	for _, v := range p {
		ret += v.a * v.b
	}
	return ret
}
func mergeIntervals(p []Pair) []Pair {
	sortPairs(p, true, true, true)
	pa, pb := p[0].a, p[0].b
	ret := make([]Pair, 0)
	for i := 0; i < len(p); i++ {
		if pb >= p[i].a {
			chmax(&pb, p[i].b)
		} else {
			ret = append(ret, Pair{pa, pb})
			pa, pb = p[i].a, p[i].b
		}
		if i == len(p)-1 {
			ret = append(ret, Pair{pa, pb})
		}
	}
	return ret
} // 複数の[a,b)の区間について重複する区間をマージする

// 無向グラフを連結成分毎にグルーピングする (1-indexedでノード0は無視)
func divideConnectedGroup(n int, p []Pair) [][]int {
	uf := NewUnionFind(n + 1)
	for i := 0; i < len(p); i++ {
		uf.Union(p[i].a, p[i].b)
	}
	nm := make(map[int][]int)
	for i := 1; i <= n; i++ {
		k := uf.find(i)
		nm[k] = append(nm[k], i)
	}
	ret := make([][]int, 0)
	for _, v := range nm {
		ret = append(ret, v)
	}
	return ret
}

// ベクトル
type Point struct{ y, x float64 }

func degreeToRadian(d float64) float64 { return d * math.Pi / 180 }
func rotatePoint(p Point, rad float64) Point {
	cos := math.Cos(rad)
	sin := math.Sin(rad)
	return Point{sin*p.x + cos*p.y, cos*p.x - sin*p.y}
}
func addPoint(a, b Point) Point         { return Point{a.y + b.y, a.x + b.x} }
func subPoint(a, b Point) Point         { return Point{a.y - b.y, a.x - b.x} }
func mulPoint(a Point, b float64) Point { return Point{a.y * b, a.x * b} }
func distance(a, b Point) float64 {
	t := subPoint(a, b)
	return math.Hypot(t.x, t.y)
}

// 図形判定
func isConnectedCircle(p1, p2 Pair, r1, r2 int) bool {
	d := distPair(p1, p2)
	if d > pow(r1+r2, 2) || d < pow(r1-r2, 2) {
		return false
	}
	return true
}

// sizeビットのうち、1がx個ある値を返すイテレータ(クロージャ)を返す。全て返した後は 0 を返し続ける。
func bitIterator(x, size int) func() int {
	if x <= 0 || x > size {
		return nil
	}
	start := (1 << x) - 1
	limit := 1 << size
	c := start
	first := true

	return func() int {
		if c >= limit {
			return 0
		}
		if first {
			first = false
			return c
		}
		u := c & -c
		v := c + u
		if v >= limit {
			c = limit
			return 0
		}
		c = (((v ^ c) >> 2) / u) | v
		if c >= limit {
			return 0
		}
		return c
	}
}

// nextPermutation()を呼び出すクロージャーを返す
func nextPermIterator(orderdSlice []int) func() []int {
	x := orderdSlice
	first := true
	f := func(x sort.Interface) bool {
		n := x.Len() - 1
		if n < 1 {
			return false
		}
		j := n - 1
		for ; !x.Less(j, j+1); j-- {
			if j == 0 {
				return false
			}
		}
		l := n
		for !x.Less(j, l) {
			l--
		}
		x.Swap(j, l)
		for k, l := j+1, n; k < l; {
			x.Swap(k, l)
			k++
			l--
		}
		return true
	}
	f2 := func() []int {
		if first == true {
			first = false
			return x
		} else {
			ret := f(sort.IntSlice(x))
			if ret == false {
				return nil
			}
			return x
		}
	}
	return f2
}

// nCkのパターン列挙用イテレーター
func nCkIterator(n, k int) func() []int {
	perm := make([]int, k)
	for i := 0; i < k; i++ {
		perm[i] = i
	}
	f := func() []int {
		for ti := k - 1; ti >= 0; ti-- {
			if perm[ti]+k-ti < n {
				if ti == k-1 {
					perm[ti]++
					return perm
				}
				perm[ti]++
				for ti2 := ti + 1; ti2 < k; ti2++ {
					perm[ti2] = perm[ti2-1] + 1
				}
				return perm
			}
		}
		return nil
	}
	return f
}

// 幅kのスライド最小値,最大値のindexのスライスを返す
func slideMaxMin(a []int, k int) ([]int, []int) {
	deq := make([]int, 0, len(a))
	deq = append(deq, 0)
	deq2 := make([]int, 0, len(a))
	deq2 = append(deq2, 0)

	retMax := make([]int, 0)
	retMin := make([]int, 0)

	for i := 0; i < len(a); i++ {
		for len(deq) > 0 && a[i] >= a[deq[len(deq)-1]] {
			deq = deq[:len(deq)-1]
		}
		for len(deq2) > 0 && a[i] <= a[deq2[len(deq2)-1]] {
			deq2 = deq2[:len(deq2)-1]
		}
		deq = append(deq, i)
		deq2 = append(deq2, i)
		if i < k-1 {
			continue
		}
		if deq[0] == i-k {
			deq = deq[1:]
		}
		if deq2[0] == i-k {
			deq2 = deq2[1:]
		}
		retMax = append(retMax, a[deq[0]])
		retMin = append(retMin, a[deq2[0]])
	}
	return retMin, retMax
}

// スライスのk幅でcが含まれる個数の最大と最小をかえす
func sliceWideCount[T ~byte | ~int](s []T, k int, c T) (int, int) {
	cur := 0
	for i := 0; i < k; i++ {
		if s[i] == c {
			cur++
		}
	}
	cMax := cur
	cMin := cur
	for i := k; i < len(s); i++ {
		if s[i] == c {
			cur++
		}
		if s[i-k] == c {
			cur--
		}
		chmax(&cMax, cur)
		chmin(&cMin, cur)
	}
	return cMin, cMax
}
