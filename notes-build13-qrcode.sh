

# ok I wanna try build13 w/ QR code and see if it works
#  extract src again too (entirely new src dir)

make LLVM=1 menuconfig    # fails b/c no clang (use as test to make sure I install it properly)
    bash -c "$(wget -O - https://apt.llvm.org/llvm.sh)"   # from https://apt.llvm.org/

    sudo update-alternatives --install /usr/bin/clang clang /usr/bin/clang-18 100
    sudo update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-18 100
    sudo update-alternatives --install /usr/bin/ld.lld ld.lld /usr/bin/ld.lld-18 100
    sudo update-alternatives --install /usr/bin/llvm-readelf llvm-readelf /usr/bin/llvm-readelf-18 100
    sudo update-alternatives --install /usr/bin/llvm-objcopy llvm-objcopy /usr/bin/llvm-objcopy-18 100
    sudo update-alternatives --install /usr/bin/llvm-nm llvm-nm /usr/bin/llvm-nm-18 100
    sudo update-alternatives --install /usr/bin/llvm-ar llvm-ar /usr/bin/llvm-ar-18 100
    sudo update-alternatives --install /usr/bin/llvm-strip llvm-strip /usr/bin/llvm-strip-18 100
    sudo update-alternatives --install /usr/bin/llvm-objdump llvm-objdump /usr/bin/llvm-objdump-18 100

    make LLVM=1 menuconfig # WORKS!

    # FYI copies current config and that is from panic screen kernel so these are already set correctly:
    cat .config   | grep DRM_PANIC
    # CONFIG_DRM_PANIC=y
    # CONFIG_DRM_PANIC_FOREGROUND_COLOR=0xffffff   # default already...
    # CONFIG_DRM_PANIC_BACKGROUND_COLOR=0x0000ff # red this time :)
    # CONFIG_DRM_PANIC_DEBUG=y
    # CONFIG_DRM_PANIC_SCREEN="user"

    # use red bg
    sed -i 's/CONFIG_DRM_PANIC_BACKGROUND_COLOR=.*/CONFIG_DRM_PANIC_BACKGROUND_COLOR=0xff0000/' .config

# install rust
make LLVM=1 rustavailable  # fails, see message for help
# Rust compiler 'rustc' could not be found.

# QUICK START - RUST https://docs.kernel.org/rust/quick-start.html # linux docs for methods to install rust

    # install rustup: https://rustup.rs/
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    # Enter for standard install
    # output:
    #    To get started you may need to restart your current shell.
    #    This would reload your PATH environment variable to include
    #    Cargo's bin directory ($HOME/.cargo/bin).
    #
    #    To configure your current shell, you need to source
    #    the corresponding env file under $HOME/.cargo.
    #
    #    This is usually done by running one of the following (note the leading DOT):
    #    . "$HOME/.cargo/env"            # For sh/bash/zsh/ash/dash/pdksh
    #    source "$HOME/.cargo/env.fish"  # For fish
    #
    # FYI bashrc sources cargo env (was added in install)
    cat ~/.bashrc | grep cargo
    #    . "$HOME/.cargo/env"
    # exit and restart shell
    #
    rustc --version
    rustup --version
    rustup show # default is stable-x86_64-unknown-linux-gnu

    # rust bindings:
    make LLVM=1 rustavailable # FAILS => Rust bindings generator 'bindgen' could not be found.
    #
    # install via bindgen-cli
    cargo install --list # no bindgen-cli
    cargo install --locked bindgen-cli
        cargo install --list # SHOWS!!!

    make LLVM=1 rustavailable # FAILS => Source code for the 'core' standard library could not be found
    rustup component add rust-src # per quick start guide

    make LLVM=1 rustavailable # WORKS => Rust is available!
