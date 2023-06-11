---
title: Podman container networking demo
nav_order: 2
---

* Table of contents
{:toc}

## Before we begin

All commands in this demo are run as `root`. Because of limitations when running as a non-`root` user, rootless Podman uses a very different mechanism to configure container networking (see "[Basic Networking Guide for Podman][basic-networking]" for details).

[basic-networking]: https://github.com/containers/podman/blob/main/docs/tutorials/basic_networking.md#differences-between-rootful-and-rootless-container-networking

## Create a container

Goal: Understand how the network environment for a container closely resembles
what we built by hand in the previous demo.

### Examine initial network configuration

<!-- file: demo2-ex1.sh -->
```sh
ip addr
```

Result:

```console
[root@node1 ~]# ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 52:54:00:de:05:13 brd ff:ff:ff:ff:ff:ff
    altname enp0s6
    altname ens6
    inet 192.168.121.67/24 brd 192.168.121.255 scope global dynamic noprefixroute eth0
       valid_lft 3564sec preferred_lft 3564sec
    inet6 fe80::3200:2118:d891:2387/64 scope link noprefixroute
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 52:54:00:45:68:7e brd ff:ff:ff:ff:ff:ff
    altname enp0s7
    altname ens7
    inet 10.0.0.11/24 brd 10.0.0.255 scope global dynamic noprefixroute eth1
       valid_lft 3564sec preferred_lft 3564sec
    inet6 fe80::cd6a:6e22:6a43:a341/64 scope link noprefixroute
       valid_lft forever preferred_lft forever
```

### Create a container

<!-- file: demo2-ex1.sh -->
```sh
podman run -d --rm --replace --name web1 --hostname web1 -p 8080:80 \
  ghcr.io/larsks/whoami:latest
```

Result:

```console
[root@node1 ~]# podman ps
CONTAINER ID  IMAGE                         COMMAND     CREATED        STATUS        PORTS                 NAMES
f0611c1e72ee  ghcr.io/larsks/whoami:latest              5 minutes ago  Up 5 minutes  0.0.0.0:8080->80/tcp  web1
```

### Examine changes to network configuration

There's a new `podman0` bridge with a `veth` interface attached:

<!-- file: demo2-ex1.sh -->
```sh
ip addr show podman0
ip link show master podman0
```

Result:

```console
4: podman0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
    link/ether fe:41:5e:4a:0d:50 brd ff:ff:ff:ff:ff:ff
    inet 10.88.0.1/16 brd 10.88.255.255 scope global podman0
       valid_lft forever preferred_lft forever
    inet6 fe80::b0a0:95ff:feb9:3815/64 scope link
       valid_lft forever preferred_lft forever
[root@node1 ~]# ip link show master podman0
5: veth0@if2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master podman0 state UP mode DEFAULT group default qlen 1000
    link/ether be:61:e0:f4:9f:e2 brd ff:ff:ff:ff:ff:ff link-netns netns-833f4c4b-c818-fc03-8bca-10c8f593fd9e
```

And a new namespace:

<!-- file: demo2-ex1.sh -->
```sh
ip netns
```

Result:

```console
[root@node1 ~]# ip netns
netns-833f4c4b-c818-fc03-8bca-10c8f593fd9e (id: 0)
```

### Examine container network configuration

Using `podman exec`:

<!-- file: demo2-ex1.sh -->
```sh
podman exec web1 ip addr
```

Result:

```console
[root@node1 ~]# podman exec web1 ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0@if5: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue state UP qlen 1000
    link/ether 5a:5c:7c:2d:31:83 brd ff:ff:ff:ff:ff:ff
    inet 10.88.0.2/16 brd 10.88.255.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::585c:7cff:fe2d:3183/64 scope link
       valid_lft forever preferred_lft forever
```

Using `nsenter`:

<!-- file: demo2-ex1.sh -->
{% raw %}
```sh
web1_pid=$(podman inspect web1 -f '{{.State.Pid}}')
nsenter -t $web1_pid -n ip addr
```
{% endraw %}

Result:

{% raw %}
```console
[root@node1 ~]# web1_pid=$(podman inspect web1 -f '{{.State.Pid}}')
[root@node1 ~]# nsenter -t $web1_pid -n ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0@if5: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
    link/ether 5a:5c:7c:2d:31:83 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.88.0.2/16 brd 10.88.255.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::585c:7cff:fe2d:3183/64 scope link
       valid_lft forever preferred_lft forever
```
{% endraw %}

### Examine iptables rules

<!-- file: demo2-ex1.sh -->
```sh
iptables -t nat -S
```

Result:

```console
[root@node1 ~]# iptables -t nat -S
-P PREROUTING ACCEPT
-P INPUT ACCEPT
-P OUTPUT ACCEPT
-P POSTROUTING ACCEPT
-N NETAVARK-1D8721804F16F
-N NETAVARK-DN-1D8721804F16F
-N NETAVARK-HOSTPORT-DNAT
-N NETAVARK-HOSTPORT-MASQ
-N NETAVARK-HOSTPORT-SETMARK
-A PREROUTING -m addrtype --dst-type LOCAL -j NETAVARK-HOSTPORT-DNAT
-A OUTPUT -m addrtype --dst-type LOCAL -j NETAVARK-HOSTPORT-DNAT
-A POSTROUTING -j NETAVARK-HOSTPORT-MASQ
-A POSTROUTING -s 10.88.0.0/16 -j NETAVARK-1D8721804F16F
-A NETAVARK-1D8721804F16F -d 10.88.0.0/16 -j ACCEPT
-A NETAVARK-1D8721804F16F ! -d 224.0.0.0/4 -j MASQUERADE
-A NETAVARK-DN-1D8721804F16F -s 10.88.0.0/16 -p tcp -m tcp --dport 8080 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-1D8721804F16F -s 127.0.0.1/32 -p tcp -m tcp --dport 8080 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-1D8721804F16F -p tcp -m tcp --dport 8080 -j DNAT --to-destination 10.88.0.2:80
-A NETAVARK-HOSTPORT-DNAT -p tcp -m tcp --dport 8080 -m comment --comment "dnat name: podman id: 8fd7accef563107a4971be4f1058880d45f0f9d5ff89a773f4a77f65fb91441b" -j NETAVARK-DN-1D8721804F16F
-A NETAVARK-HOSTPORT-MASQ -m comment --comment "netavark portfw masq mark" -m mark --mark 0x2000/0x2000 -j MASQUERADE
-A NETAVARK-HOSTPORT-SETMARK -j MARK --set-xmark 0x2000/0x2000
```

### Examine sysctl settings

```console
[root@node1 ~]# sysctl -a -r podman0.route_localnet
net.ipv4.conf.podman0.route_localnet = 1
```

We see the same `route_localnet` setting we saw in the namespace demo.

## Publish on different ports

Goal: Understand how to expose services on different host ports.

### Start containers

<!-- file: demo2-ex4.sh -->
```sh
podman run -d --rm --replace --name web1 --hostname web1 -p 8080:80 \
  --network mynetwork ghcr.io/larsks/whoami:latest
podman run -d --rm --replace --name web2 --hostname web2 -p 8081:80 \
  --network mynetwork ghcr.io/larsks/whoami:latest
```

### Demonstrate access from host

<!-- file: demo2-ex4.sh -->
```sh
curl http://localhost:8080
curl http://localhost:8081
```

Result:

```console
[root@node1 ~]# curl http://localhost:8080
Hostname: web1
IP: 127.0.0.1
IP: ::1
IP: 10.89.0.6
IP: fe80::840:4ff:fe21:d9eb
RemoteAddr: 10.89.0.1:58528
GET / HTTP/1.1
Host: localhost:8080
User-Agent: curl/8.0.1
Accept: */*
[root@node1 ~]# curl http://localhost:8081
Hostname: web2
IP: 127.0.0.1
IP: ::1
IP: 10.89.0.7
IP: fe80::e82d:96ff:fe02:bc8c
RemoteAddr: 10.89.0.1:33582
GET / HTTP/1.1
Host: localhost:8081
User-Agent: curl/8.0.1
Accept: */*
```

### Examine iptables rules

<!-- file: demo2-ex4.sh -->
```sh
iptables -t nat -S
```

Result:

```console
[root@node1 ~]# iptables -t nat -S
...
-A NETAVARK-DN-741C6CD328516 -s 10.89.0.0/24 -p tcp -m tcp --dport 8080 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-741C6CD328516 -s 127.0.0.1/32 -p tcp -m tcp --dport 8080 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-741C6CD328516 -p tcp -m tcp --dport 8080 -j DNAT --to-destination 10.89.0.6:80
-A NETAVARK-DN-741C6CD328516 -s 10.89.0.0/24 -p tcp -m tcp --dport 8081 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-741C6CD328516 -s 127.0.0.1/32 -p tcp -m tcp --dport 8081 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-741C6CD328516 -p tcp -m tcp --dport 8081 -j DNAT --to-destination 10.89.0.7:80
...
```

## Publish on different addresses

Goal: Understand how to expose services on different host addresses.

### Configure additional addresses

<!-- file: demo2-ex5.sh -->
```sh
ip addr add 192.168.121.200/24 dev eth0
ip addr add 192.168.121.201/24 dev eth0
ip addr show eth0
```

Result:

```console
[root@node1 ~]# ip addr show eth0
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 52:54:00:de:05:13 brd ff:ff:ff:ff:ff:ff
    altname enp0s6
    altname ens6
    inet 192.168.121.67/24 brd 192.168.121.255 scope global dynamic noprefixroute eth0
       valid_lft 1991sec preferred_lft 1991sec
    inet 192.168.121.200/24 scope global secondary eth0
       valid_lft forever preferred_lft forever
    inet 192.168.121.201/24 scope global secondary eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::3200:2118:d891:2387/64 scope link noprefixroute
       valid_lft forever preferred_lft forever
```

### Start containers

<!-- file: demo2-ex5.sh -->
```sh
podman run -d --rm --replace --name web1 --hostname web1 -p 192.168.121.200:80:80 \
  ghcr.io/larsks/whoami:latest
podman run -d --rm --replace --name web2 --hostname web2 -p 192.168.121.201:80:80 \
  ghcr.io/larsks/whoami:latest
```

Result:

```console
[root@node1 ~]# podman ps
CONTAINER ID  IMAGE                       COMMAND     CREATED        STATUS        PORTS                       NAMES
d8c01a597b12  ghcr.io/larsks/whoami:latest  whoami      2 seconds ago  Up 2 seconds  192.168.121.200:80->80/tcp  web1
6af21b2fc41c  ghcr.io/larsks/whoami:latest  whoami      1 second ago   Up 2 seconds  192.168.121.201:80->80/tcp  web2
```

### Examine iptables rules:

```
[root@node1 ~]# iptables -t nat -S
...
-A NETAVARK-DN-1D8721804F16F -s 10.88.0.0/16 -d 192.168.121.200/32 -p tcp -m tcp --dport 80 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-1D8721804F16F -s 127.0.0.1/32 -d 192.168.121.200/32 -p tcp -m tcp --dport 80 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-1D8721804F16F -d 192.168.121.200/32 -p tcp -m tcp --dport 80 -j DNAT --to-destination 10.88.0.3:80
-A NETAVARK-DN-1D8721804F16F -s 10.88.0.0/16 -d 192.168.121.201/32 -p tcp -m tcp --dport 80 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-1D8721804F16F -s 127.0.0.1/32 -d 192.168.121.201/32 -p tcp -m tcp --dport 80 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-1D8721804F16F -d 192.168.121.201/32 -p tcp -m tcp --dport 80 -j DNAT --to-destination 10.88.0.4:80
...
```

### Confirm access from host

<!-- file: demo2-ex5.sh -->
```sh
curl http://192.168.121.200
curl http://192.168.121.201
```

Result:

```console
[root@node1 ~]# curl http://192.168.121.200
Hostname: web1
IP: 127.0.0.1
IP: ::1
IP: 10.89.0.12
IP: fe80::14f1:3fff:fed8:ee3d
RemoteAddr: 192.168.121.67:56658
GET / HTTP/1.1
Host: 192.168.121.200
User-Agent: curl/8.0.1
Accept: */*
[root@node1 ~]# curl http://192.168.121.201
Hostname: web2
IP: 127.0.0.1
IP: ::1
IP: 10.89.0.13
IP: fe80::48b2:3cff:fed9:395a
RemoteAddr: 192.168.121.67:45438
GET / HTTP/1.1
Host: 192.168.121.201
User-Agent: curl/8.0.1
Accept: */*
```

## Domain name lookups on user-defined networks

Goal: Show that DNS lookups work on user defined networks, but not on the
default network.

### Create two containers

<!-- file: demo2-ex2.sh -->
```sh
podman run -d --rm --replace --name web1 --hostname web1 ghcr.io/larsks/whoami:latest
podman run -d --rm --replace --name web2 --hostname web2 ghcr.io/larsks/whoami:latest
```

Result:

```console
[root@node1 ~]# podman ps
CONTAINER ID  IMAGE                       COMMAND     CREATED        STATUS        PORTS       NAMES
26ecdb0cfd06  ghcr.io/larsks/whoami:latest  whoami      3 seconds ago  Up 3 seconds              web1
85578efbceb5  ghcr.io/larsks/whoami:latest  whoami      3 seconds ago  Up 3 seconds              web2
```

### Show name lookup failure

<!-- file: demo2-ex2.sh -->
```sh
podman exec web1 curl -sS web2
```

Result:

```console
[root@node1 ~]# podman exec web1 curl -sS  web2
curl: (6) Could not resolve host: web2
```

### Create user-defined network

<!-- file: demo2-ex2.sh -->
```sh
podman network create mynetwork
```

Result:

```console
[root@node1 ~]# podman network ls
NETWORK ID    NAME        DRIVER
9fa7b113aa45  mynetwork   bridge
2f259bab93aa  podman      bridge
```

### Create containers attached to network

<!-- file: demo2-ex2.sh -->
```sh
podman run --replace --name web1 --hostname web1 -d \
  --network mynetwork ghcr.io/larsks/whoami:latest
podman run --replace --name web2 --hostname web2 -d \
  --network mynetwork ghcr.io/larsks/whoami:latest
```

### Show name lookup success

<!-- file: demo2-ex2.sh -->
```sh
podman exec web1 curl -sS web2
```

Result:

```console
[root@node1 ~]# podman exec web1 curl -sS web2
Hostname: web2
IP: 127.0.0.1
IP: ::1
IP: 10.89.0.3
IP: fe80::38f5:edff:fe7a:91b4
RemoteAddr: 10.89.0.2:40910
GET / HTTP/1.1
Host: web2
User-Agent: curl/8.1.2
Accept: */*
```
