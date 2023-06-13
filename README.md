---
nav_order: 0
permalink: index.html
---

# Container networking

This content is published automatically at <http://oddbit.com/container-networking-slides/>.

## Presentation

- [Presentation](presentation.html)

## Demos

- [Network namespaces](demo1-linux-bridge/index.md)
- [Podman containers](demo2-podman-networking/index.md)
- [OpenVSwitch](demo3-openvswitch/index.md)

## Conventions used in this repository

```
These are commands you should type in verbatim
```

```console
This is an example shell session with command output
```

## Setting up the demo environment

If you want to reproduce these demos, you will need:

- [Libvirt](https://libvirt.org)
- [Vagrant](https://www.vagrantup.com/)
- The Vagrant [libvirt provider](https://github.com/vagrant-libvirt/vagrant-libvirt)
- [Ansible](https://www.ansible.com)

If things are installed and configured correctly, you should be able to set up the demo environment by running:

```
vagrant up
```

You can then connect to the demo node by running:

- `vagrant ssh node1`
- `vagrant ssh node2`
