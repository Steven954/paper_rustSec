# FFIChecker container image for deterministic builds/runs
FROM debian:bullseye

ENV RUSTUP_DIST_SERVER=https://mirrors.ustc.edu.cn/rust-static \
    RUSTUP_UPDATE_ROOT=https://mirrors.ustc.edu.cn/rustup \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH \
    RUSTUP_TOOLCHAIN=nightly-2021-12-05 \
    RUSTUP_HTTP_TIMEOUT=600 \
    RUSTUP_USE_CURL=1 \
    LLVM_SYS_130_PREFIX=/usr/lib/llvm-13 \
    LLVM_CONFIG_PATH=/usr/bin/llvm-config-13 \
    CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse \
    CARGO_REGISTRIES_CRATES_IO_INDEX=https://mirrors.ustc.edu.cn/crates.io-index \
    CARGO_NET_GIT_FETCH_WITH_CLI=true \
    CARGO_HTTP_MULTIPLEXING=false \
    CARGO_HTTP_TIMEOUT=600

# Use faster/more reliable mirrors inside the image
RUN set -eux; \
    sed -i 's|http://deb.debian.org/debian|http://mirrors.ustc.edu.cn/debian|g' /etc/apt/sources.list; \
    sed -i 's|http://security.debian.org/debian-security|http://mirrors.ustc.edu.cn/debian-security|g' /etc/apt/sources.list

RUN set -eux; \
    apt-get update || ( \
      sed -i 's|http://mirrors.ustc.edu.cn/debian|http://mirrors.tuna.tsinghua.edu.cn/debian|g' /etc/apt/sources.list; \
      sed -i 's|http://mirrors.ustc.edu.cn/debian-security|http://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list; \
      apt-get update || ( \
        sed -i 's|http://mirrors.tuna.tsinghua.edu.cn/debian|http://deb.debian.org/debian|g' /etc/apt/sources.list; \
        sed -i 's|http://mirrors.tuna.tsinghua.edu.cn/debian-security|http://security.debian.org/debian-security|g' /etc/apt/sources.list; \
        apt-get update \
      ) \
    ); \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      curl ca-certificates git \
      llvm-13-dev libclang-common-13-dev clang clang-13 lld lld-13 \
      build-essential pkg-config cmake zlib1g-dev || ( \
      sed -i 's|http://mirrors.ustc.edu.cn/debian|http://mirrors.tuna.tsinghua.edu.cn/debian|g' /etc/apt/sources.list; \
      sed -i 's|http://mirrors.ustc.edu.cn/debian-security|http://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list; \
      apt-get update || ( \
        sed -i 's|http://mirrors.tuna.tsinghua.edu.cn/debian|http://deb.debian.org/debian|g' /etc/apt/sources.list; \
        sed -i 's|http://mirrors.tuna.tsinghua.edu.cn/debian-security|http://security.debian.org/debian-security|g' /etc/apt/sources.list; \
        apt-get update \
      ); \
      DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git \
        llvm-13-dev libclang-common-13-dev clang clang-13 lld lld-13 \
        build-essential pkg-config cmake zlib1g-dev \
    ); \
    ln -s /usr/bin/llvm-as-13 /usr/local/bin/llvm-as || true; \
    rm -rf /var/lib/apt/lists/*

# Install Rust via rustup binary (nightly 2021-12-05) and required components
RUN set -eux; \
    curl -fL -sS --retry 5 --retry-delay 3 --retry-connrefused \
      https://mirrors.ustc.edu.cn/rustup/archive/1.27.0/x86_64-unknown-linux-gnu/rustup-init -o /tmp/rustup-init || \
    curl -fL -sS --retry 5 --retry-delay 3 --retry-connrefused \
      https://mirrors.ustc.edu.cn/rust-static/rustup/archive/1.27.0/x86_64-unknown-linux-gnu/rustup-init -o /tmp/rustup-init || \
    curl -fL -sS --retry 5 --retry-delay 3 --retry-connrefused \
      http://mirrors.ustc.edu.cn/rust-static/rustup/archive/1.27.0/x86_64-unknown-linux-gnu/rustup-init -o /tmp/rustup-init || \
    curl -fL -sS --retry 5 --retry-delay 3 --retry-connrefused \
      https://rsproxy.cn/rustup/archive/1.27.0/x86_64-unknown-linux-gnu/rustup-init -o /tmp/rustup-init || \
    curl -fL -sS --retry 5 --retry-delay 3 --retry-connrefused \
      https://static.rust-lang.org/rustup/archive/1.27.0/x86_64-unknown-linux-gnu/rustup-init -o /tmp/rustup-init; \
    chmod +x /tmp/rustup-init; \
    installed=0; \
    for i in 1 2 3; do \
      if RUSTUP_INIT_SKIP_PATH_CHECK=yes CARGO_HOME=/usr/local/cargo RUSTUP_HOME=/usr/local/rustup /tmp/rustup-init -y --no-modify-path --profile minimal --default-toolchain ${RUSTUP_TOOLCHAIN}; then \
        installed=1; \
        break; \
      fi; \
      echo "rustup-init failed (ustc), retry $i" >&2; \
      rm -rf /usr/local/cargo /usr/local/rustup; \
      sleep 5; \
    done; \
    if [ "$installed" -ne 1 ]; then \
      RUSTUP_DIST_SERVER=https://static.rust-lang.org RUSTUP_UPDATE_ROOT=https://static.rust-lang.org/rustup \
        RUSTUP_INIT_SKIP_PATH_CHECK=yes CARGO_HOME=/usr/local/cargo RUSTUP_HOME=/usr/local/rustup /tmp/rustup-init -y --no-modify-path --profile minimal --default-toolchain ${RUSTUP_TOOLCHAIN}; \
    fi; \
    ls -l /usr/local/cargo/bin; \
    /usr/local/cargo/bin/rustup --version; \
    added=0; \
    for i in 1 2 3; do \
      if /usr/local/cargo/bin/rustup component add rustc-dev llvm-tools-preview --toolchain ${RUSTUP_TOOLCHAIN}; then \
        added=1; \
        break; \
      fi; \
      echo "rustup component add failed (ustc), retry $i" >&2; \
      sleep 5; \
    done; \
    if [ "$added" -ne 1 ]; then \
      RUSTUP_DIST_SERVER=https://static.rust-lang.org /usr/local/cargo/bin/rustup component add rustc-dev llvm-tools-preview --toolchain ${RUSTUP_TOOLCHAIN}; \
    fi; \
    /usr/local/cargo/bin/rustup default ${RUSTUP_TOOLCHAIN}; \
    rm /tmp/rustup-init

WORKDIR /opt/rust-ffi-checker
COPY . .

# Build and install binaries once into the image for faster subsequent runs
RUN set -eux; \
    git config --global url."https://mirrors.ustc.edu.cn/crates.io-index".insteadOf https://github.com/rust-lang/crates.io-index; \
    built=0; \
    for i in 1 2 3; do \
      if /usr/local/cargo/bin/cargo +${RUSTUP_TOOLCHAIN} build --release --locked --bin entry_collector --features driver && \
         /usr/local/cargo/bin/cargo +${RUSTUP_TOOLCHAIN} build --release --locked --bin cargo-ffi-checker --features driver && \
         /usr/local/cargo/bin/cargo +${RUSTUP_TOOLCHAIN} build --release --locked --bin analyzer --features analysis; then \
        built=1; \
        break; \
      fi; \
      echo "cargo install failed (ustc), retry $i" >&2; \
      sleep 5; \
    done; \
    if [ "$built" -ne 1 ]; then \
      echo "cargo build failed after retries" >&2; \
      exit 1; \
    fi; \
    install -m 0755 target/release/entry_collector /usr/local/cargo/bin/entry_collector; \
    install -m 0755 target/release/cargo-ffi-checker /usr/local/cargo/bin/cargo-ffi-checker; \
    install -m 0755 target/release/analyzer /usr/local/cargo/bin/analyzer; \
    rm -rf target

ENTRYPOINT ["/bin/bash"]
