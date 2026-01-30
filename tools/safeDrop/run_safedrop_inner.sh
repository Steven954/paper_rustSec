set -e
set -o pipefail
set -x

SAFEDROP_SRC=/workspace/safedrop
SAFEDROP_HOME=/workspace/safedrop-home
RUST_SRC="$SAFEDROP_HOME/rust"
RUST_TAG="1.63.0"
TARGET_IS_DIR="0"
TARGET_PATH="/workspace/target/tmp_double_free.rs"

mkdir -p "$SAFEDROP_HOME"
mkdir -p "$SAFEDROP_HOME/cargo-home"
echo "SAFEDROP_HOME=$SAFEDROP_HOME"
echo "RUST_SRC=$RUST_SRC"
echo "TARGET_PATH=$TARGET_PATH"
echo "TARGET_IS_DIR=$TARGET_IS_DIR"
uname -a || true
df -h || true
free -h || true

if [ ! -d "$RUST_SRC/.git" ]; then
  echo "Cloning rust-lang/rust..."
  time git clone https://github.com/rust-lang/rust.git "$RUST_SRC"
fi

cd "$RUST_SRC"
lock="$RUST_SRC/.git/index.lock"
if [ -f "$lock" ]; then
  echo "Removing stale git lock: $lock"
  rm -f "$lock"
fi
echo "Fetching tags..."
fetch_ok=0
if time git fetch --tags --force; then
  fetch_ok=1
else
  echo "git fetch failed, retrying with GIT_SSL_NO_VERIFY=1..."
  if time GIT_SSL_NO_VERIFY=1 git fetch --tags --force; then
    fetch_ok=1
  fi
fi
if [ "$fetch_ok" -ne 1 ]; then
  echo "git fetch still failed; continuing with existing tags."
fi
if ! git show-ref --tags --verify --quiet "refs/tags/$RUST_TAG"; then
  echo "Tag $RUST_TAG not found locally. Fetch failed or tag missing."
  exit 1
fi
echo "Checkout tag $RUST_TAG..."
time git checkout -f "$RUST_TAG"
echo "Cleaning untracked files to match tag..."
time git reset --hard
  time git clean -fdx -e build/cache
echo "Re-checkout tag $RUST_TAG after clean..."
time git checkout -f "$RUST_TAG"
git -c color.ui=never status -sb -uno || true
git -c color.ui=never rev-parse HEAD || true
git -c color.ui=never describe --tags --always || true

echo "Applying SafeDrop patch..."
time python3 "$SAFEDROP_SRC/scripts/apply_safedrop_patch.py" --rust-src "$RUST_SRC" --safedrop-src "$SAFEDROP_SRC"

host=""
if [ -d build ]; then
  host=$(ls -1 build | grep -E 'unknown' | head -n 1 || true)
fi
if [ -z "$host" ] || [ ! -x "build/$host/stage1/bin/rustc" ]; then
  echo "Building stage1 rustc..."
  if [ "x$SAFEDROP_FORCE_NIGHTLY" = "x1" ] && command -v rustup >/dev/null 2>&1; then
    if ! rustup toolchain list | grep -q "nightly-2022-06-30"; then
      echo "Installing nightly-2022-06-30 toolchain for bootstrap..."
      install_ok=0
      for dist in \
        "https://mirrors.ustc.edu.cn/rust-static|https://mirrors.ustc.edu.cn/rustup" \
        "https://rsproxy.cn|https://rsproxy.cn/rustup" \
        "https://static.rust-lang.org|https://static.rust-lang.org/rustup"; do
        dist_server=$(printf "%s" "$dist" | cut -d'|' -f1)
        update_root=$(printf "%s" "$dist" | cut -d'|' -f2)
        for i in 1 2 3; do
          if RUSTUP_DIST_SERVER="$dist_server" RUSTUP_UPDATE_ROOT="$update_root" \
            rustup toolchain install nightly-2022-06-30; then
            install_ok=1
            break
          fi
          sleep 3
        done
        if [ "$install_ok" -eq 1 ]; then
          break
        fi
      done
      if [ "$install_ok" -ne 1 ]; then
        echo "Failed to install nightly-2022-06-30 toolchain from all mirrors."
        exit 1
      fi
    fi
    export RUSTUP_TOOLCHAIN=nightly-2022-06-30
    export CARGO="$(rustup which cargo)"
    export RUSTC="$(rustup which rustc)"
    echo "Bootstrap CARGO=$CARGO"
    echo "Bootstrap RUSTC=$RUSTC"
    if [ -n "$CARGO" ] && [ -n "$RUSTC" ]; then
      cat > "$RUST_SRC/config.toml" <<EOF
cargo = "$CARGO"
rustc = "$RUSTC"
EOF
    fi
  else
    unset CARGO
    unset RUSTC
    unset RUSTUP_TOOLCHAIN
    cat > "$RUST_SRC/config.toml" <<'EOF'
[llvm]
ninja = false
download-ci-llvm = false
EOF
    if [ -f "$RUST_SRC/library/Cargo.toml" ]; then
      echo "Temporarily moving library/Cargo.toml to avoid nested workspace errors..."
      python3 - <<'PY'
from pathlib import Path

path = Path("library/Cargo.toml")
bak = Path("library/Cargo.toml.safedrop-bak")
if path.exists():
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.unlink()
PY
    fi
  fi
  if [ -f .gitmodules ]; then
    while read -r sub_path; do
      if [ -n "$sub_path" ] && [ -d "$sub_path" ] && [ ! -e "$sub_path/.git" ]; then
        echo "Cleaning partial submodule: $sub_path"
        rm -rf "$sub_path" ".git/modules/$sub_path"
        mkdir -p "$sub_path"
      fi
    done < <(git config -f .gitmodules --get-regexp path | awk '{print $2}')
  fi
  if [ -d src/llvm-project ]; then
    echo "Resetting llvm-project submodule workspace..."
    rm -rf src/llvm-project .git/modules/src/llvm-project
    mkdir -p src/llvm-project
  fi
  llvm_lock="$RUST_SRC/.git/modules/src/llvm-project/index.lock"
  if [ -f "$llvm_lock" ]; then
    echo "Removing stale submodule lock: $llvm_lock"
    rm -f "$llvm_lock"
  fi
  llvm_shallow_lock="$RUST_SRC/.git/modules/src/llvm-project/shallow.lock"
  if [ -f "$llvm_shallow_lock" ]; then
    echo "Removing stale submodule lock: $llvm_shallow_lock"
    rm -f "$llvm_shallow_lock"
  fi
  llvm_lock2="$RUST_SRC/src/llvm-project/.git/index.lock"
  if [ -f "$llvm_lock2" ]; then
    echo "Removing stale submodule lock: $llvm_lock2"
    rm -f "$llvm_lock2"
  fi
  llvm_shallow_lock2="$RUST_SRC/src/llvm-project/.git/shallow.lock"
  if [ -f "$llvm_shallow_lock2" ]; then
    echo "Removing stale submodule lock: $llvm_shallow_lock2"
    rm -f "$llvm_shallow_lock2"
  fi
  build_ok=0
  export GIT_SSL_NO_VERIFY=1
  echo "Using GIT_SSL_NO_VERIFY=$GIT_SSL_NO_VERIFY"
  if [ -n "$SAFEDROP_CRATES_IO_INDEX" ]; then
    crates_index="$SAFEDROP_CRATES_IO_INDEX"
  else
    crates_index="https://mirrors.tuna.tsinghua.edu.cn/git/crates.io-index.git"
  fi
  export CARGO_REGISTRIES_CRATES_IO_INDEX="$crates_index"
  echo "Using CARGO_REGISTRIES_CRATES_IO_INDEX=$CARGO_REGISTRIES_CRATES_IO_INDEX"
  export CARGO_HOME="$SAFEDROP_HOME/cargo-home"
  mkdir -p "$CARGO_HOME"
  cat > "$CARGO_HOME/config.toml" <<EOF
[source.crates-io]
replace-with = "rsproxy"

[source.rsproxy]
registry = "$crates_index"
EOF
  cat > "$CARGO_HOME/config" <<EOF
[source.crates-io]
replace-with = "rsproxy"

[source.rsproxy]
registry = "$crates_index"
EOF
  if [ -n "$SAFEDROP_DIST_MIRRORS" ]; then
    dist_list="$SAFEDROP_DIST_MIRRORS"
  else
    dist_list="https://static.rust-lang.org https://rsproxy.cn https://mirrors.ustc.edu.cn/rust-static"
  fi
  for dist in $dist_list; do
    export RUSTUP_DIST_SERVER="$dist"
    echo "Using RUSTUP_DIST_SERVER=$RUSTUP_DIST_SERVER"
    if time python3 x.py build --stage 1 compiler/rustc; then
      build_ok=1
      break
    fi
    echo "x.py build failed with RUSTUP_DIST_SERVER=$RUSTUP_DIST_SERVER, trying next mirror..."
  done
  if [ "$build_ok" -ne 1 ]; then
    echo "x.py build failed for all mirrors."
    exit 1
  fi
fi

host=$(ls -1 build | grep -E 'unknown' | head -n 1)
stage1="$RUST_SRC/build/$host/stage1"

if [ "$TARGET_IS_DIR" = "1" ]; then
  if [ ! -x "$stage1/bin/cargo" ]; then
    echo "Building stage1 cargo..."
    time python3 x.py build --stage 1 src/tools/cargo
  fi
  export RUSTC="$stage1/bin/rustc"
  export CARGO_HOME="$SAFEDROP_HOME/cargo-home"
  echo "Building Cargo project..."
  time "$stage1/bin/cargo" build --manifest-path "$TARGET_PATH/Cargo.toml"
else
  echo "Running rustc on single file..."
  time "$stage1/bin/rustc" "$TARGET_PATH"
fi