use std::fs::File;
use std::io::{self, Read};
use std::path::Path;

pub fn read_file(file_path: &str) -> io::Result<Vec<u8>> {
    let path = Path::new(file_path);
    let mut file = File::open(&path)?;
    let mut buffer = Vec::new();
    file.read_to_end(&mut buffer)?;
    Ok(buffer)
}

#[macro_export]
macro_rules! log {
    ($($arg:tt)*) => {
        #[cfg(debug_assertions)]
        {
            println!($($arg)*);
        }
    };
}
