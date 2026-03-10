fn main() {
    let mut reader = contest_input::UncheckedInput::batch();
    let mut writer = contest_output::BufferedOutput::new();

    let s = reader.read_string();
    let mut num = 0;
    for symbol in s {
        match symbol {
            b'-' => {
                num -= 1;
            }
            b'+' => {
                num += 1;
            }
            _ => {}
        }
    }
    writer.print(num);
}

mod contest_input {
    #![allow(dead_code, unsafe_op_in_unsafe_fn)]
    use std::io::Read;

    pub struct UncheckedInput<B: Backend> {
        backend: B,
    }

    impl UncheckedInput<BatchBackend> {
        #[inline]
        pub fn batch() -> Self {
            Self {
                backend: BatchBackend::new(),
            }
        }
    }

    impl UncheckedInput<InteractiveBackend> {
        #[inline]
        pub fn interactive() -> Self {
            Self {
                backend: InteractiveBackend::new(),
            }
        }
    }

    impl<B: Backend> UncheckedInput<B> {
        #[inline(always)]
        pub fn read_int<T: Int>(&mut self) -> T {
            unsafe { T::parse(&mut self.backend) }
        }

        #[inline(always)]
        pub fn read_string(&mut self) -> Vec<u8> {
            unsafe { self.backend.read_string() }
        }
    }

    pub trait Backend {
        unsafe fn has_next(&self) -> bool;
        unsafe fn peek(&self) -> u8;
        unsafe fn advance(&mut self);
        unsafe fn skip_whitespace(&mut self);
        unsafe fn read_string(&mut self) -> Vec<u8>;
    }

    pub struct BatchBackend {
        buf: Vec<u8>,
        idx: usize,
    }

    impl BatchBackend {
        #[inline]
        fn new() -> Self {
            let mut buf = Vec::with_capacity(0x100000);
            std::io::stdin().read_to_end(&mut buf).unwrap();
            Self { buf, idx: 0 }
        }
    }

    impl Backend for BatchBackend {
        #[inline(always)]
        unsafe fn has_next(&self) -> bool {
            self.idx < self.buf.len()
        }

        #[inline(always)]
        unsafe fn peek(&self) -> u8 {
            debug_assert!(self.has_next());
            *self.buf.get_unchecked(self.idx)
        }

        #[inline(always)]
        unsafe fn advance(&mut self) {
            self.idx += 1;
        }

        #[inline(always)]
        unsafe fn skip_whitespace(&mut self) {
            while self.has_next() && *self.buf.get_unchecked(self.idx) <= b' ' {
                self.idx += 1;
            }
        }

        #[inline(always)]
        unsafe fn read_string(&mut self) -> Vec<u8> {
            self.skip_whitespace();
            let start = self.idx;
            while self.has_next() && *self.buf.get_unchecked(self.idx) > b' ' {
                self.idx += 1;
            }
            self.buf[start..self.idx].to_vec()
        }
    }

    pub struct InteractiveBackend {
        buf: [u8; 0x100000],
        pos: usize,
        len: usize,
    }

    impl InteractiveBackend {
        #[inline]
        fn new() -> Self {
            Self {
                buf: [0; 0x100000],
                pos: 0,
                len: 0,
            }
        }

        #[inline(always)]
        unsafe fn refill(&mut self) {
            if self.has_next() {
                return;
            }
            self.len = std::io::stdin().read(&mut self.buf).unwrap();
            self.pos = 0;
            debug_assert!(self.len > 0, "interactive input exhausted");
        }
    }

    impl Backend for InteractiveBackend {
        #[inline(always)]
        unsafe fn has_next(&self) -> bool {
            self.pos < self.len
        }

        #[inline(always)]
        unsafe fn peek(&self) -> u8 {
            *self.buf.get_unchecked(self.pos)
        }

        #[inline(always)]
        unsafe fn advance(&mut self) {
            self.pos += 1;
            self.refill();
        }

        #[inline(always)]
        unsafe fn skip_whitespace(&mut self) {
            loop {
                self.refill();
                if !self.has_next() || *self.buf.get_unchecked(self.pos) > b' ' {
                    break;
                }
                self.pos += 1;
            }
        }

        #[inline(always)]
        unsafe fn read_string(&mut self) -> Vec<u8> {
            self.skip_whitespace();
            let mut out = Vec::new();
            loop {
                self.refill();
                if self.has_next() {
                    let c = *self.buf.get_unchecked(self.pos);
                    if c <= b' ' {
                        break;
                    }
                    out.push(c);
                    self.pos += 1;
                }
            }
            out
        }
    }

    pub trait Int {
        unsafe fn parse<B: Backend>(backend: &mut B) -> Self;
    }

    macro_rules! impl_unsigned {
        ($($t:ty),*) => {$(
            impl Int for $t {
                #[inline(always)]
                unsafe fn parse<B: Backend>(b: &mut B) -> Self {
                    b.skip_whitespace();
                    let mut val: $t = 0;
                    loop {
                        if !b.has_next() {
                            break;
                        }
                        let c = b.peek();
                        if c < b'0' {
                            break;
                        }
                        val = val * 10 + (c - b'0') as $t;
                        b.advance();
                    }
                    val
                }
            }
        )*};
    }

    macro_rules! impl_signed {
        ($($t:ty),*) => {$(
            impl Int for $t {
                #[inline(always)]
                unsafe fn parse<B: Backend>(b: &mut B) -> Self {
                    b.skip_whitespace();
                    if b.has_next() {
                        let mut neg = false;
                        if b.peek() == b'-' {
                            neg = true;
                            b.advance();
                        }
                        let mut val: $t = 0;
                        loop {
                            if !b.has_next() {
                                break;
                            }
                            let c = b.peek();
                            if c < b'0' {
                                break;
                            }
                            val = val * 10 + (c - b'0') as $t;
                            b.advance();
                        }
                        return if neg { -val } else { val };
                    }
                    unreachable!()
                }
            }
        )*};
    }

    impl_unsigned!(u8, u16, u32, u64, usize);
    impl_signed!(i8, i16, i32, i64, isize);
}

mod contest_output {
    #![allow(dead_code)]
    use std::io::{self, Write};

    pub struct BufferedOutput {
        buf: io::BufWriter<io::Stdout>,
    }

    impl BufferedOutput {
        #[inline(always)]
        pub fn new() -> Self {
            Self {
                buf: io::BufWriter::with_capacity(0x100000, io::stdout()),
            }
        }

        #[inline(always)]
        pub fn print<T: std::fmt::Display>(&mut self, x: T) {
            write!(self.buf, "{}", x).unwrap();
        }

        #[inline(always)]
        pub fn println<T: std::fmt::Display>(&mut self, x: T) {
            writeln!(self.buf, "{}", x).unwrap();
        }

        #[inline(always)]
        pub fn print_bytes(&mut self, bytes: &[u8]) {
            self.buf.write_all(bytes).unwrap();
        }

        #[inline(always)]
        pub fn flush(&mut self) {
            self.buf.flush().unwrap();
        }
    }
}
