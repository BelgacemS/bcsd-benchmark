use proconio::{fastout, input};

#[fastout]
fn main() {
    input! {
        n: usize,
        m: usize,
        xyz: [(i64, i64, i64); n],
    }
    let mut sums = vec![Vec::with_capacity(n); 8];
    for i in 0..n {
        let (x, y, z) = xyz[i];
        let ppp = x + y + z;
        let ppn = x + y - z;
        let pnp = x - y + z;
        let npp = -x + y + z;
        let pnn = x - y - z;
        let npn = -x + y - z;
        let nnp = -x - y + z;
        let nnn = -x - y - z;
        sums[0].push((ppp, i));
        sums[1].push((ppn, i));
        sums[2].push((pnp, i));
        sums[3].push((npp, i));
        sums[4].push((pnn, i));
        sums[5].push((npn, i));
        sums[6].push((nnp, i));
        sums[7].push((nnn, i));
    }

    for i in 0..8 {
        sums[i].sort();
        sums[i].reverse();
    }

    let mut ans = 0;
    for i in 0..8 {
        let mut sum_x = 0;
        let mut sum_y = 0;
        let mut sum_z = 0;
        for j in 0..m {
            let (_, idx) = sums[i][j];
            let (x, y, z) = xyz[idx];
            sum_x += x;
            sum_y += y;
            sum_z += z;
        }

        ans = ans.max(sum_x.abs() + sum_y.abs() + sum_z.abs());
    }

    println!("{}", ans);
}
