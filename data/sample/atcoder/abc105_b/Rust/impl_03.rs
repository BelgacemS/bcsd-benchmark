use proconio::input;

fn main() {
    input! {
        n: usize
    }

    for i in 0.. {
        if i * 4 > n {
            break;
        }
        if (n - i * 4) % 7 == 0 {
            println!("Yes");
            return;
        }
    }
    println!("No");
}
