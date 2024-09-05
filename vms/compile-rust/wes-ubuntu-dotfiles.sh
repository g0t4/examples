# assumes sudoers access setup, and run script as the lowly user you want to setup (i.e. vagrant user, or wes user , or w/e)
# alternatively I could enumerate all users in /home and usually that would be just one and do all of them

# TODO move these to my dotfiles repo so I can keep it there
touch $HOME/.hushlogin
sudo touch /root/.hushlogin

sudo apt update # optional
sudo apt install -y fish golang
# todo what is this from:
#   Ignoring file 'ubuntu.sources.curtin.old' in directory '/etc/apt/sources.list.d/' as it has an invalid filename extension
#

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

# todo only once / copy it
curl -L https://iterm2.com/shell_integration/install_shell_integration.sh | bash
curl -L https://iterm2.com/shell_integration/install_shell_integration.sh | sudo bash
