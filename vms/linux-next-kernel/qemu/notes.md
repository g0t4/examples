```bash


qemu-img create -f qcow2 disk1.qcow2 100G

virsh define u2410.xml
virsh start u2410

# connect
virsh console u2410 # connect in terminal (works well)
virsh vncdisplay u2410 # shows port used, 0 == 5900 (default) ... localhost
ssh wes@localhost -p 2222 # connect over SSH, setup wes user during ubuntu installer (imported SSH keys too)
scp -P 2222 foo.txt wes@localhost:. # scp in uses -P port flag (rest of ssh args work too beyond these - options, identity file, etc)

# remove
virsh destroy u2410 # force shutdown
virsh destroy u2410
virsh undefine u2410 --nvram


# list info:
virsh list # domains
virsh domblklist u2410 # blk devices
virsh domiflist u2410 # returns nothing :( ... why

# I manually installed ubuntu .... it's fast as F ... wow qemu is rocking for virtualization on my mac (TODO try out amd64 emulation next)

virsh capabilities # show what is supported

```

## NOTES

- formatdomain docs seems to cover most of what I have in my domain xml definition:
  - https://libvirt.org/formatdomain.html#disk
