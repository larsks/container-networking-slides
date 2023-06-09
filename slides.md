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
- Same processor architecture*

---

# What's a namespace?

Containers are built from one or more *namespaces*:

- A way of partitioning kernel resources
- A typical container uses at least:

  - Mount
  - Network
  - PID
  - User
  - UTS (hostname)

- We're going to focus on network namespaces

---

# Namespaces: Tools we will use

- [`ip`](https://man7.org/linux/man-pages/man8/ip.8.html)

  The `ip` command manages network interface configuration and persistent
  network namespaces. See also [`ip link`](https://man7.org/linux/man-pages/man8/ip-link.8.html),
  [`ip route`](https://man7.org/linux/man-pages/man8/ip-route.8.html), and 
  [`ip netns`](https://man7.org/linux/man-pages/man8/ip-netns.8.html).

- [`unshare`](https://man7.org/linux/man-pages/man1/unshare.1.html)

  The `unshare` command is a general purpose wrapper for the `unshare`
  system call, which allows a process to isolate itself in various
  namespaces.

---

# Namespaces: Tools we will use

- [`nsenter`](https://man7.org/linux/man-pages/man1/nsenter.1.html)

  The `nsenter` command allows you to run commands in existing namespaces.

- [`tcpdump`](https://man7.org/linux/man-pages/man1/tcpdump.1.html)

  `tcpdump` is a tool for inspecting network traffic.

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

(Unlike the previous example, this namespace is ephemeral -- it will go away when the main process exits.)

Run a shell in a new filesystem root with isolated mount, pid, and network namespaces:

```
unshare -R /srv/alpine --mount --pid --net \
  --fork --mount-proc /bin/sh
```

---

# Running a command in a namespace with nsenter

Run a command in the network namespace of another process:

```
nsenter -t <pid> -n <command>
```

Or in the network and pid namespaces:

```
nsenter -t <pid> -n -p <command>
```

Etc.

---

# Physical networking

- Physical Interfaces
- Cables
- Switches
- Routers

---

# Virtual networking

- Physical interfaces
  - `eth0`
  - `enp0s31f6`
- Virtual interfaces
  - `veth` devices
  - OpenVSwitch ports
  - VXLAN/Geneve tunnels
- Bridge devices (virtual switches)
  - Linux bridges
  - OpenVSwitch bridges
- Kernel (routing and firewall rules)


---

# Demo 1: Network namespaces and bridge devices

[Demo 1](demo1-linux-bridge)

---

# Demo 2: Networking in Podman

[Demo 2](demo2-podman-networking)

---

# Demo 3: OpenVSwitch

[Demo 3](demo3-openvswitch)

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
ip link set <interface> master <bridge_device>
```

For example:

```
ip link set eth0 master br-example
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

Show detailed bridge configuration

```
ip -d link show <bridge_device>
```

---

# Getting information about  a bridge

```
[root@node1 ~]# ip -d link show podman1
30: podman1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default qlen 1000
    link/ether c2:de:ac:15:4d:94 brd ff:ff:ff:ff:ff:ff promiscuity 0  allmulti 0 minmtu 68 maxmtu 65535
    bridge forward_delay 1500 hello_time 200 max_age 2000 ageing_time 30000
    stp_state 0 priority 32768 vlan_filtering 0 vlan_protocol 802.1Q bridge_id
    8000.c2:de:ac:15:4d:94 designated_root 8000.c2:de:ac:15:4d:94 root_port 0
    root_path_cost 0 topology_change 0 topology_change_detected 0 hello_timer
    0.00 tcn_timer    0.00 topology_change_timer    0.00 gc_timer    3.44
    vlan_default_pvid 1 vlan_stats_enabled 0 vlan_stats_per_port 0
    group_fwd_mask 0 group_address 01:80:c2:00:00:00 mcast_snooping 1
    no_linklocal_learn 0 mcast_vlan_snooping 0 mcast_router 1
    mcast_query_use_ifaddr 0 mcast_querier 0 mcast_hash_elasticity 16
    mcast_hash_max 4096 mcast_last_member_count 2 mcast_startup_query_count 2
    mcast_last_member_interval 100 mcast_membership_interval 26000
    mcast_querier_interval 25500 mcast_query_interval 12500
    mcast_query_response_interval 1000 mcast_startup_query_interval 3125
    mcast_stats_enabled 0 mcast_igmp_version 2 mcast_mld_version 1
    nf_call_iptables 0 nf_call_ip6tables 0 nf_call_arptables 0 addrgenmode
    eui64 numtxqueues 1 numrxqueues 1 gso_max_size 65536 gso_max_segs 65535
    tso_max_size 524280 tso_max_segs 65535 gro_max_size 65536
```

---

# Veth devices

A [`veth`][veth] device is like a virtual patch cable: it consists of two endpoints that are effectively two ends of a wire.

[veth]: https://man7.org/linux/man-pages/man4/veth.4.html

---

# Creating a veth device

```
ip link add name left type veth peer name right [netns <nsname>]
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
