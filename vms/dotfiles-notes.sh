# config of common elements in my linux learning envs
#

# *** ROOT dotfiles
# change root's shell too, I hate bash, such a PITA to `sudo su`, now it is wonderful!
sudo chsh -s /usr/bin/fish root
sudo touch ~/.hushlogin
# FYI my modified fish_prompt_modified includes code to use # for root user
sudo git clone https://github.com/g0t4/dotfiles.git /root/repos/github/g0t4/dotfiles
sudo ln --force -s /root/repos/github/g0t4/dotfiles/fish/config/config.fish /root/.config/fish/config.fish  # link to my fish config, logout/in to source
sudo fish -c "source /root/repos/github/g0t4/dotfiles/fish/install/install.fish"
# todo install some tools globally, i.e.: osc
sudo go install -v github.com/theimpostor/osc@latest
curl -L https://iterm2.com/shell_integration/install_shell_integration.sh | sudo bash # or use iterm2 menu to do this
