use proconio::input;

fn main() {
    input! {
        n: usize, m: usize,
        cakes: [(i64, i64, i64); n],
    }

    let inf = 1i64 << 60;
    let mut ans = -inf;

    for bits in 0..1 << 3 {
        let mut dp = vec![-inf; m + 1];
        dp[0] = 0;
        for &(x, y, z) in &cakes {
            let x = if bits >> 0 & 1 == 0 { -x } else { x };
            let y = if bits >> 1 & 1 == 0 { -y } else { y };
            let z = if bits >> 2 & 1 == 0 { -z } else { z };

            for i in (1..=m).rev() {
                if dp[i - 1] != inf {
                    dp[i] = dp[i].max(dp[i - 1] + x + y + z);
                }
            }
        }

        ans = ans.max(dp[m]);
    }

    println!("{ans}");
}
