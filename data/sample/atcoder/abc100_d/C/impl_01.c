#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

typedef struct {
  int_fast64_t x;
  int_fast64_t y;
  int_fast64_t z;
} cake_t;

static int compare (
    const void * a,
    const void * b
) {
  const int_fast64_t * ia = (int_fast64_t *)a;
  const int_fast64_t * ib = (int_fast64_t *)b;
  if (*ia < *ib) {
    return +1;
  } else {
    return -1;
  }
}

static void * memory_alloc (
    const size_t nitems,
    const size_t size
) {
  void * ptr = malloc(nitems * size);
  if (NULL == ptr) {
    printf("memory allocation error: %zu x %zu\n", nitems, size);
    exit(EXIT_FAILURE);
  }
  return ptr;
}

static int_fast64_t my_max (
    const int_fast64_t a,
    const int_fast64_t b
) {
  return b < a ? a : b;
}

static int process (
    const int n,
    const int m,
    cake_t * cakes
) {
  int_fast64_t * sums = memory_alloc(n, sizeof(int_fast64_t));
  int_fast64_t max_sum = 0;
  for (size_t pattern = 0; pattern < (1 << 3); pattern++) {
    // check 8 combinations:
    //   + x + y + z
    //   - x + y + z
    //   ...
    //   + x - y - z
    //   - x - y - z
    for (int i = 0; i < n; i++) {
      const cake_t * cake = cakes + i;
      int_fast64_t x = cake->x;
      int_fast64_t y = cake->y;
      int_fast64_t z = cake->z;
      if (1 & (pattern >> 0)) {
        x = -x;
      }
      if (1 & (pattern >> 1)) {
        y = -y;
      }
      if (1 & (pattern >> 2)) {
        z = -z;
      }
      sums[i] = x + y + z;
    }
    qsort(sums, n, sizeof(int_fast64_t), compare);
    int_fast64_t sum = 0;
    for (int i = 0; i < m; i++) {
      sum += sums[i];
    }
    max_sum = my_max(max_sum, sum);
  }
  printf("%lld\n", max_sum);
  free(sums);
  return 0;
}

int main (
    void
) {
  // load stdin
  int n = 0, m = 0;
  if (2 != scanf("%d %d", &n, &m)) {
    puts("invalid input");
    exit(EXIT_FAILURE);
  }
  cake_t * cakes = memory_alloc(n, sizeof(cake_t));
  for (int i = 0; i < n; i++) {
    cake_t * cake = cakes + i;
    int_fast64_t x = 0, y = 0, z = 0;
    if (3 != scanf("%lld %lld %lld", &x, &y, &z)) {
      puts("invalid input");
      exit(EXIT_FAILURE);
    }
    cake->x = x;
    cake->y = y;
    cake->z = z;
  }
  process(n, m, cakes);
  free(cakes);
  return 0;
}
