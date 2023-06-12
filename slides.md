class: middle, center

# Container Networking

Lars Kellogg-Stedman <lars@redhat.com>

.nodecoration[
- Slides: <http://oddbit.com/container-networking-slides/>
- Source: <https://github.com/larsks/container-networking-slides>
]

---

# Let's create a container!

```
podman run -d --rm -p 8080:80 --name web1 \
  ghcr.io/larsks/whoami:latest
```

- `-d` -- run in the background
- `--rm` -- delete container when it exits
- `-p 8080:80` -- publish container port 80 on host port 8080
- `--name web1` -- give the container a name

---

# Let's create a container!

```
podman run -d --rm -p 8080:80 --name web1 \
  ghcr.io/larsks/whoami:latest
```

- We can access the web service at `http://localhost:8080`
- And also at `http://<hostname_or_ip>:8080`
- Even from remote hosts!

What's going on? How does it work?

---

# What's  a container?

A container is just a process with a restricted view of available resources:

- Different hostname
- Different root filesystem
- Different network configuration

--

...but:

- Same kernel
- Same devices
- Same processor architecture

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

# Creating a network namespace

Run a shell with an isolated network namespace:

```
ip netns add example
ip netns exec example bash
```

We don't have any networking at this point, so it's not terribly useful:

```
[root@node1 ~]# ip addr
1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
```

--

This isn't the only way to create a network namespace. See also the [unshare][] command.

[unshare]: https://man7.org/linux/man-pages/man1/unshare.1.html

---

# Running a command in an existing namespace

For named namespaces (things we can see with `ip netns`):

```
ip netns exec <namespace> <command> ...
```

Run a command in the network namespace of another process:

```
nsenter -t <pid> -n <command> ...
```

---

class: middle, center

# Getting things connected

---

# Physical networking

- Physical Interfaces
- Cables
- Switches
- Routers

---

# Virtual networking

- Virtual interfaces
  - `veth` devices
  - OpenVSwitch ports
  - VXLAN/Geneve tunnels
- Bridge devices (virtual switches)
  - Linux bridges
  - OpenVSwitch bridges
- Kernel (routing and firewall rules)

---

class: middle, center

# Demos

---

# Demo 1: Network namespaces and bridge devices

We look at how to set up a namespace with both inbound and outbound network connectivity so that it can:

- Communicate with other namespaces
- Communicate with the host
- Communicate with remote systems
- Provide network services

[Demo 1](demo1-linux-bridge)

---

# Demo 2: Networking in Podman

We look in detail at Podman containers and notice how remarkably similar they are to the namespaces we created by hand in the previous demo.

[Demo 2](demo2-podman-networking)

---

# Demo 3: OpenVSwitch

We look at OpenVSwitch, which is used in both OpenStack and OpenShift to create virtual networks spanning multiple nodes.

[Demo 3](demo3-openvswitch)
