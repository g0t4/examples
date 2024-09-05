
# bit more space
lsblk
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
df -h
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv

# clone linux-next
git clone https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git $HOME/linux-next

# override "ubuntu" default hostname
sudo hostnamectl set-hostname compile-rust



# host:
vagrant snapshot save linux-next


# kernel build deps:
sudo apt install -y build-essential libncurses-dev bison flex libssl-dev libelf-dev

# setup initial config:
cd $HOME/linux-next
cp -v /boot/config-$(uname -r) .config
yes "" | make localmodconfig # strip down to local h/w modules/drivers... and answer default to questions
#
grep "SYSTEM_.*_KEYS" .config # check
scripts/config --set-str CONFIG_SYSTEM_TRUSTED_KEYS ""
scripts/config --set-str CONFIG_SYSTEM_REVOCATION_KEYS ""
#
mkdir $HOME/configs
cp .config $HOME/configs/01-localmodconfig.config # for comparison later on


# check if LLVM is working:
make LLVM=1 menuconfig
# => clang: not found
# install llvm/clang:
sudo bash -c "$(wget -O - https://apt.llvm.org/llvm.sh)"
# validate:
llvm-config-18 --version
clang-18 --version
# NOTE might be newer version than 18, adjust accordingly

make LLVM=1 menuconfig # check again
# => still => clang: not found
make LLVM=-18 menuconfig # check again
#   => exit dont save changes
#   IIRC its recommended to use LLVM if building with rust support, gcc is experimental IIRC

make LLVM=-18 rustavailable
# => Rust compiler 'rustc' could not be found.
#   => fix issues one by one
# install rustup:
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# proceed with standard installation
# exit shell / start new shell (b/c rustup is cached as not avail)
rustup --version # works
rustc --version # works
rustup show

make LLVM=-18 rustavailable
# => Rust bindings generator 'bindgen' could not be found.
cargo install --list # no bindgen-cli
cargo install --locked bindgen-cli
    cargo install --list # SHOWS!!!

make LLVM=-18 rustavailable
# => Source code for the 'core' standard library could not be found
rustup component add rust-src

make LLVM=-18 rustavailable
make rustavailable # FYI this can work too to test for rust support
make LLVM=1 rustavailable # However, this will report "unknown C compiler"
