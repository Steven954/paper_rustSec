use std::mem::ManuallyDrop;
use std::ptr;

// Panic-safe variant using ManuallyDrop to avoid double free.
unsafe fn ok<F: FnOnce()>(v: Vec<u8>, f: F) {
    let mut v = ManuallyDrop::new(v);
    let _dup = ptr::read(&*v); // duplicate without automatic drop
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(f));
    // Always forget the duplicate; no double free on unwind.
    std::mem::forget(_dup);
    // Explicitly drop once.
    ManuallyDrop::drop(&mut v);
    let _ = result; // ignore panic for this demo
}

fn main() {
    let v = vec![10, 20, 30];
    unsafe {
        ok(v, || {
            if 2 + 2 == 4 { panic!("boom"); }
        });
    }
}
