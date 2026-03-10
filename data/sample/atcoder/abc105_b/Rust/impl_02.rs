use proconio::input;

fn main() {
    input! {
        n: i32,
    }
    let mut is_found = false;
    for i in 0..=n {
        let rest = n - 7 * i;
        if rest >= 0 && rest % 4 == 0 {
            is_found = true;
            break;
        }
    }
    if is_found {
        println!("Yes");
    } else {
        println!("No");
    }
}
