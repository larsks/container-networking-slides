---
title: Linux namespaces demo
---

## Basic namespace setup

<!-- file: demo1-ex1.sh -->

Goal: Create two namespaces connected to the same virtual network. Demonstrate
that the two namespaces are able to communicate.

### Create bridge

Add a Linux bridge device:

```sh
ip link add br0 type bridge
```

Result:

```console
[root@node1 ~]# ip link show br0
4: br0: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether 9a:b5:85:9a:ad:c5 brd ff:ff:ff:ff:ff:ff
```

### Create namespaces

```sh
ip netns add ns1
ip netns add ns2
```

Result:

```console
[root@node1 ~]# ip netns
ns2 (id: 1)
ns1 (id: 0)
```

### Create veth devices

```sh
ip link add ns1-ext type veth peer name ns1-int netns ns1
ip link add ns2-ext type veth peer name ns2-int netns ns2
```

Result:

```console
[root@node1 ~]# ip link show type veth
5: ns1-ext@if2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br0 state UP mode DEFAULT group default qlen 1000
    link/ether d6:69:bd:06:9c:fa brd ff:ff:ff:ff:ff:ff link-netns ns1
6: ns2-ext@if2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br0 state UP mode DEFAULT group default qlen 1000
    link/ether ce:10:da:46:71:fb brd ff:ff:ff:ff:ff:ff link-netns ns2
[root@node1 ~]# ip -n ns1 link show type veth
2: ns1-int@if5: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default qlen 1000
    link/ether 02:1c:91:28:d0:ed brd ff:ff:ff:ff:ff:ff link-netnsid 0
[root@node1 ~]# ip -n ns2 link show type veth
2: ns2-int@if6: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default qlen 1000
    link/ether ee:c7:5b:94:08:73 brd ff:ff:ff:ff:ff:ff link-netnsid 0
```

### Add vif devices to bridge

```sh
ip link set master br0 dev ns1-ext
ip link set master br0 dev ns2-ext
```

Result:

```console
[root@node1 ~]# ip link show master br0
5: ns1-ext@if2: <BROADCAST,MULTICAST> mtu 1500 qdisc noop master br0 state DOWN mode DEFAULT group default qlen 1000
    link/ether d6:69:bd:06:9c:fa brd ff:ff:ff:ff:ff:ff link-netns ns1
6: ns2-ext@if2: <BROADCAST,MULTICAST> mtu 1500 qdisc noop master br0 state DOWN mode DEFAULT group default qlen 1000
    link/ether ce:10:da:46:71:fb brd ff:ff:ff:ff:ff:ff link-netns ns2
```

### Assign addresses to internal interfaces

```sh
ip -n ns1 addr add 192.168.255.11/24 dev ns1-int
ip -n ns2 addr add 192.168.255.12/24 dev ns2-int
```

Result:

```console
[root@node1 ~]# ip -n ns1 addr show
1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: ns1-int@if5: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN group default qlen 1000
    link/ether 76:af:dc:95:bd:cb brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 192.168.255.11/24 scope global ns1-int
       valid_lft forever preferred_lft forever
[root@node1 ~]# ip -n ns2 addr show
1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: ns2-int@if6: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN group default qlen 1000
    link/ether b2:9b:26:e8:b3:01 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 192.168.255.12/24 scope global ns2-int
       valid_lft forever preferred_lft forever
```

###  Show communication between namespaces

```sh
ip netns exec ns1 ping -c2 192.168.255.12
ip netns exec ns2 ping -c2 192.168.255.11
```

Result:

```console
[root@node1 ~]# ip netns exec ns1 ping -c2 192.168.255.12
ping: connect: Network is unreachable
[root@node1 ~]# ip netns exec ns2 ping -c2 192.168.255.11
ping: connect: Network is unreachable
```

We need to bring up all the interfaces before they will pass traffic:

```sh
ip link set br0 up
ip link set ns1-ext up
ip link set ns2-ext up
ip -n ns1 link set lo up
ip -n ns1 link set ns1-int up
ip -n ns2 link set lo up
ip -n ns2 link set ns2-int up
```

Now retry `ping` commands:

```console
[root@node1 ~]# ip netns exec ns1 ping -c2 192.168.255.12
PING 192.168.255.12 (192.168.255.12) 56(84) bytes of data.
64 bytes from 192.168.255.12: icmp_seq=1 ttl=64 time=0.065 ms
64 bytes from 192.168.255.12: icmp_seq=2 ttl=64 time=0.034 ms

--- 192.168.255.12 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1001ms
rtt min/avg/max/mdev = 0.034/0.049/0.065/0.015 ms
[root@node1 ~]# ip netns exec ns2 ping -c2 192.168.255.11
PING 192.168.255.11 (192.168.255.11) 56(84) bytes of data.
64 bytes from 192.168.255.11: icmp_seq=1 ttl=64 time=0.016 ms
64 bytes from 192.168.255.11: icmp_seq=2 ttl=64 time=0.048 ms

--- 192.168.255.11 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1022ms
rtt min/avg/max/mdev = 0.016/0.032/0.048/0.016 ms
```

## Communication with the host

<!-- file: demo1-ex2.sh -->

Goal: Allow the namespaces to successfully communicate with the host.

### Show failure to communicate with host

```sh
host_address="$(ip route | sed -n '/default/ s/.*src \([^ ]*\).*/\1/p;q')"
ip netns exec ns1 ping -c2 $host_address
```

Result:

```console
ping: connect: Network is unreachable
```

The namespace doesn't know how to reach the host.

### Add address to bridge

```sh
ip addr add 192.168.255.1/24 dev br0
```

Result:

```console
[root@node1 ~]# ip addr show br0
4: br0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
    link/ether ce:10:da:46:71:fb brd ff:ff:ff:ff:ff:ff
    inet 192.168.255.1/24 scope global br0
       valid_lft forever preferred_lft forever
    inet6 fe80::cc10:daff:fe46:71fb/64 scope link
       valid_lft forever preferred_lft forever
```

### Add default route to namespaces

```sh
ip -n ns1 route add default via 192.168.255.1
ip -n ns2 route add default via 192.168.255.1
```

Result:

```console
[root@node1 ~]# ip -n ns1 route
default via 192.168.255.1 dev ns1-int
192.168.255.0/24 dev ns1-int proto kernel scope link src 192.168.255.11
[root@node1 ~]# ip -n ns2 route
default via 192.168.255.1 dev ns2-int
192.168.255.0/24 dev ns2-int proto kernel scope link src 192.168.255.12
```

### Show successful communication with host

```sh
host_address="$(ip route | sed -n '/default/ s/.*src \([^ ]*\).*/\1/p;q')"
ip netns exec ns1 ping -c2 $host_address
```

Result:

```console
[root@node1 ~]# host_address="$(ip route | sed -n '/default/ s/.*src \([^ ]*\).*/\1/p;q')"
[root@node1 ~]# ip netns exec ns1 ping -c2 $host_address
PING 192.168.121.67 (192.168.121.67) 56(84) bytes of data.
64 bytes from 192.168.121.67: icmp_seq=1 ttl=64 time=0.042 ms
64 bytes from 192.168.121.67: icmp_seq=2 ttl=64 time=0.056 ms

--- 192.168.121.67 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1021ms
rtt min/avg/max/mdev = 0.042/0.049/0.056/0.007 ms
```

## Communicating with remote services

<!-- file: demo1-ex3.sh -->

Goal: Allow the namespaces to communicate with remote services

### Show failure to communicate with remote address

```sh
ip netns exec ns1 ping -c2 8.8.8.8
```

Result:

```console
[root@node1 ~]# ip netns exec ns1 ping -c2 8.8.8.8
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.

--- 8.8.8.8 ping statistics ---
2 packets transmitted, 0 received, 100% packet loss, time 1005ms
```

Use `tcpdump` to see that no traffic shows up on `eth0`.

### Enable ip forwarding

```sh
sysctl -w net.ipv4.ip_forward=1
```

Use `tcpdump` to see that ICMP echo requests packets egress on `eth0`, but
they have the source address of the namespace.

```console
[root@node1 ~]# tcpdump -i eth0 -nn icmp
dropped privs to tcpdump
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on eth0, link-type EN10MB (Ethernet), snapshot length 262144 bytes
16:28:47.567601 IP 192.168.255.11 > 8.8.8.8: ICMP echo request, id 1687, seq 1, length 64
16:28:48.597039 IP 192.168.255.11 > 8.8.8.8: ICMP echo request, id 1687, seq 2, length 64
```

### Add masquerade rules on host

```sh
iptables -t nat -A POSTROUTING -s 192.168.255.0/24 -j MASQUERADE
```

Result:

```console
[root@node1 ~]# iptables -t nat -S
-P PREROUTING ACCEPT
-P INPUT ACCEPT
-P OUTPUT ACCEPT
-P POSTROUTING ACCEPT
-A POSTROUTING -s 192.168.255.0/24 -j MASQUERADE
```

### Show successful communication with remote address

```sh
ip netns exec ns1 ping -c2 8.8.8.8
```

Use `tcpdump` to see that ICMP echo request packets now use the address of `eth0` as the source address:

```console
[root@node1 ~]# tcpdump -i eth0 -nn icmp
dropped privs to tcpdump
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on eth0, link-type EN10MB (Ethernet), snapshot length 262144 bytes
16:29:34.839131 IP 192.168.121.67 > 8.8.8.8: ICMP echo request, id 27972, seq 1, length 64
16:29:34.850431 IP 8.8.8.8 > 192.168.121.67: ICMP echo reply, id 27972, seq 1, length 64
16:29:35.840854 IP 192.168.121.67 > 8.8.8.8: ICMP echo request, id 27972, seq 2, length 64
16:29:35.853196 IP 8.8.8.8 > 192.168.121.67: ICMP echo reply, id 27972, seq 2, length 64
```
