use proconio::input;

fn main() {
    input! {
        _n: usize,
        m: usize,
        data: [(i32, i32); m],
    }

    let mut segs: Vec<_> = data;
    segs.sort_unstable_by_key(|a| a.1);
    let mut count = 0;
    let mut broken: Vec<i32> = vec![];

    's: for s in segs {
        let a = s.0;
        let b = s.1;
        for br in &broken {
            if (a..b).contains(br) {
                continue 's;
            }
        }
        broken.push(b - 1);
        count += 1;
    }
    println!("{}", count);
}
