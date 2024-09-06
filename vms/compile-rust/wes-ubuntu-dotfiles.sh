# assumes sudoers access setup, and run script as the lowly user you want to setup (i.e. vagrant user, or wes user , or w/e)
# alternatively I could enumerate all users in /home and usually that would be just one and do all of them

# common apt packages
sudo apt update # optional
sudo apt install -y fish golang # necessary for below
sudo apt install -y apt-file bat command-not-found curl dnsutils git grc icdiff iproute2 \
    iputils-arping iputils-ping iputils-tracepath jq lshw lsof net-tools most \
    procps psmisc silversearcher-ag tree unzip util-linux vim wget

# todo what is this from:
#   Ignoring file 'ubuntu.sources.curtin.old' in directory '/etc/apt/sources.list.d/' as it has an invalid filename extension
#

# TODO move these to my dotfiles repo so I can keep it there
touch $HOME/.hushlogin
sudo touch /root/.hushlogin


sudo chsh -s /usr/bin/fish $USER # avoids need for password
sudo chsh -s /usr/bin/fish root

# TODO only clone once would be preferrable
git clone https://github.com/g0t4/dotfiles.git $HOME/repos/github/g0t4/dotfiles
sudo git clone https://github.com/g0t4/dotfiles.git /root/repos/github/g0t4/dotfiles

mkdir -p $HOME/.config/fish
sudo mkdir -p /root/.config/fish

ln --force -s  $HOME/repos/github/g0t4/dotfiles/fish/config/config.fish  $HOME/.config/fish/config.fish
sudo ln --force -s /root/repos/github/g0t4/dotfiles/fish/config/config.fish /root/.config/fish/config.fish
# make sure to logout / kill persistent ssh connections

fish -c "source $HOME/repos/github/g0t4/dotfiles/fish/install/install.fish"
sudo fish -c "source /root/repos/github/g0t4/dotfiles/fish/install/install.fish"

# todo install globally?
go install -v github.com/theimpostor/osc@latest
sudo go install -v github.com/theimpostor/osc@latest

# SHELL=fish (env var) is used by script to add ~/.iterm2_shell_integration.fish (not .bash)
# FYI this enables ask openai iterm tool (any remote/shell that has iterm integration)
curl -L https://iterm2.com/shell_integration/install_shell_integration.sh | SHELL=fish bash
curl -L https://iterm2.com/shell_integration/install_shell_integration.sh | sudo SHELL=fish bash


ln -s $HOME/repos/github/g0t4/dotfiles/.grc  $HOME/.grc
mkdir -p $HOME/.config/bat
ln -s $HOME/repos/github/g0t4/dotfiles/.config/bat/config  $HOME/.config/bat/config
ln -s $HOME/repos/github/g0t4/dotfiles/git/linux.gitconfig  $HOME/.gitconfig
# root:
sudo ln -s /root/repos/github/g0t4/dotfiles/.grc  /root/.grc
sudo mkdir -p /root/.config/bat
sudo ln -s /root/repos/github/g0t4/dotfiles/.config/bat/config  /root/.config/bat/config
sudo ln -s /root/repos/github/g0t4/dotfiles/git/linux.gitconfig  /root/.gitconfig
