# --dry-run dont forget to use to test
rsync --delete --archive --verbose --exclude .venv ./ build13:~/printz
