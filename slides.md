class: middle, center

# Container Networking

Lars Kellogg-Stedman <lars@redhat.com>

.nodecoration[
- Slides: <http://oddbit.com/container-networking-slides/>
- Source: <https://github.com/larsks/container-networking-slides>
]

---

# Overview

What we're going to cover today:

- What's a container?
- What are some low-level tools for creating and interacting with containers?
- What are the building blocks used to set up typical container network environments?
- How does networking work in the context of [Podman][] or Docker containers?

[podman]: https://podman.io/

---

# What's a container?

A container is just a process with a restricted view of available resources:

- Different hostname
- Different root filesystem
- Restricted set of network devices

But:

- Same kernel
- Same devices
- Same processor architecture

---

# What's a namespace?

Containers are built from one or more *namespaces*:

- A way of partitioning kernel resources
- We're going to focus on network namespaces
- A typical container uses at least:

  - Mount
  - PID
  - User
  - Network
  - UTS (hostname)

---

# Namespaces: Tools we will use

- `ip`

  The `ip` command manages network interface configuration and persistent
  network namespaces.

- `unshare`

  The `unshare` command is a general purpose wrapper for the `unshare`
  system call, which allows a process to isolate itself in various
  namespaces.

---

# Namespaces: Tools we will use

- `nsenter`

  The `nsenter` command allows you to run commands in existing namespaces.

- `systemd-nspawn`

  `systemd-nspawn` lies somewhere between `unshare` and something like Podman
  or Docker. It provides a number of convenient features (e.g., automatically
  mounting special filesystems like `/proc`) that make created functional
  namespaced processes more convenient.

---

# Look, it's a container! (ip netns)

Run a shell with an isolated network namespace:

```
ip netns add example
ip netns exec example bash
```

---

# Look, it's a container! (unshare)

Run a shell with an isolated network namespace:

```
unshare --net
```

Run a shell in a new filesystem root with isolated mount, pid, and network namespaces:

```
unshare -R /srv/alpine --mount --pid --net --fork --mount-proc /bin/sh
```

---

# Running a process in a namespace with nsenter

Run a shell in the namespace from the previous example:

```
nsenter -t <pid> -n
```

---

# Physical networking

- Physical Interfaces
- Cables
- Switches
- Routers

---

# Virtual networking

- Physical interfaces
- Virtual interfaces
- Bridge devices
- Kernel


---

# Demo 1: Network namespaces and bridge devices

[Demo 1](demo1-linux-bridge)

---

# Demo 2: Networking in Podman

[Demo 2](demo2-podman-networking)

---

# Bridge devices

A bridge device is like a virtual switch. Managed using:

- `ip` (primarily `ip link`)
- `bridge`

---

# Creating bridges devices

```
ip link add name <bridge_device> type bridge
```

For example:

```
ip link add name br-example type bridge
```

---

# Adding interfaces to a bridge

```
ip link set master <bridge_device> dev <interface>
```

For example:

```
ip link set master br-example dev eth0
```

---

# Getting information about a bridge

List bridge devices

```
ip link show type bridge
```

Show interfaces attached to a bridge

```
ip link show master <bridge_device>
```

---

# Veth devices

A [`veth`][veth] device is like a virtual patch cable: it consists of two endpoints that are effectively two ends of a wire.

[veth]: https://man7.org/linux/man-pages/man4/veth.4.html

---

# Creating a veth device

```
ip link add name left type veth peer name right
```

This results in a pair of devices:

```
$ ip link show type veth
2: right@left: <BROADCAST,MULTICAST,M-DOWN> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether 2a:c7:81:f1:41:2a brd ff:ff:ff:ff:ff:ff
3: left@right: <BROADCAST,MULTICAST,M-DOWN> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether 36:a9:a2:ea:ef:22 brd ff:ff:ff:ff:ff:ff
```

---

# Using a veth device

Generally something like:

- Create a bridge
- Create a network namespace
- Create a pair of veth devices
- Put one end inside the namespace
- Attach the other end to the bridge
