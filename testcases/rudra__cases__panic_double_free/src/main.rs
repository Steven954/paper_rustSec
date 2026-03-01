use std::ptr;

// Panic-safety bug: double free if `f` panics before we forget the original.
pub fn bad<F: FnOnce(String)>(s: String, f: F) {
    unsafe {
        let dup = ptr::read(&s); // duplicate ownership of s
        f(dup); // user-provided closure may panic while owning dup
        std::mem::forget(s); // avoid double free on normal path
    }
}

fn main() {
    let s = String::from("hello");
    bad(s, |owned| {
        let _ = owned.len();
        panic!("boom");
    });
}
