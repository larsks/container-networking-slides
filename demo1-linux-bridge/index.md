---
title: Linux namespaces demo
nav_order: 1
---

* Table of contents
{:toc}

## Basic namespace setup

Goal: Create two namespaces connected to the same virtual network. Demonstrate
that the two namespaces are able to communicate.

### Create bridge

Add a Linux bridge device:

<!-- file: demo1-ex1.sh -->
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

<!-- file: demo1-ex1.sh -->
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

<!-- file: demo1-ex1.sh -->
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

<!-- file: demo1-ex1.sh -->
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

<!-- file: demo1-ex1.sh -->
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

<!-- file: demo1-ex1.sh -->
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

<!-- file: demo1-ex1.sh -->
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

Goal: Allow the namespaces to successfully communicate with the host.

### Show failure to communicate with host

<!-- file: demo1-ex2.sh -->
```sh
ip netns exec ns1 ping -c2 node1-pub
```

Result:

```console
[root@node1 ~]# ip netns exec ns1 ping -c2 node1-pub
ping: connect: Network is unreachable
```

The namespace doesn't know how to reach the host.

### Add address to bridge

<!-- file: demo1-ex2.sh -->
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

<!-- file: demo1-ex2.sh -->
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

<!-- file: demo1-ex2.sh -->
```sh
ip netns exec ns1 ping -c2 node1-pub
```

Result:

```console
[root@node1 ~]# ip netns exec ns1 ping -c2 node1-pub
PING 192.168.121.67 (192.168.121.67) 56(84) bytes of data.
64 bytes from 192.168.121.67: icmp_seq=1 ttl=64 time=0.042 ms
64 bytes from 192.168.121.67: icmp_seq=2 ttl=64 time=0.056 ms

--- 192.168.121.67 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1021ms
rtt min/avg/max/mdev = 0.042/0.049/0.056/0.007 ms
```

## Communicating with remote services

Goal: Allow the namespaces to communicate with remote services

### Show failure to communicate with remote address

<!-- file: demo1-ex3.sh -->
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

<!-- file: demo1-ex3.sh -->
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

<!-- file: demo1-ex3.sh -->
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

<!-- file: demo1-ex3.sh -->
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

## Running a service in a namespace

Goal: Run a simple web server in a namespace. Demonstrate different ways of accessing the service.

### Start a web service in the ns1 namespace

<!-- file: demo1-ex4.sh -->
```sh
ip netns exec ns1 whoami &
```

### Access the service using the address of ns1

<!-- file: demo1-ex4.sh -->
```sh
curl 192.168.255.11
```

Result:

```console
Hostname: node1
IP: 192.168.255.11
IP: fe80::58e4:e3ff:fe74:b65
RemoteAddr: 192.168.255.1:51858
GET / HTTP/1.1
Host: 192.168.255.11
User-Agent: curl/8.0.1
Accept: */*
```

### Expose the service on a host port

Create a `PREROUTING` rule to redirect traffic to port 8080 to the service:

<!-- file: demo1-ex4.sh -->
```sh
iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 192.168.255.11:80
```

Result:

```console
[root@node1 ~]# iptables -t nat -S
-P PREROUTING ACCEPT
-P INPUT ACCEPT
-P OUTPUT ACCEPT
-P POSTROUTING ACCEPT
-A PREROUTING -p tcp -m tcp --dport 8080 -j DNAT --to-destination 192.168.255.11:80
-A POSTROUTING -s 192.168.255.0/24 -j MASQUERADE
```

### Show successful access from a "remote" host

```console
remotehost$ curl 192.168.121.67:8080
Hostname: node1
IP: 127.0.0.1
IP: ::1
IP: 192.168.255.11
IP: fe80::30b6:61ff:feae:e86e
RemoteAddr: 192.168.121.1:39824
GET / HTTP/1.1
Host: 192.168.121.67:8080
User-Agent: curl/8.0.1
Accept: */*
```

### Access from local host to public address

This attempt fails:

<!-- file: demo1-ex4.sh -->
```sh
curl --connect-timeout 10 node1-pub:8080
```

Result:

```console
curl: (7) Failed to connect to node1-pub port 8080 after 0 ms: Couldn't connect to server
```

Locally originating traffic does not traverse `PREROUTING` chain. We need an `OUTPUT` rule:

<!-- file: demo1-ex4.sh -->
```sh
iptables -t nat -A OUTPUT -p tcp --dport 8080 -j DNAT --to-destination 192.168.255.11:80
```

Previous command now succeeds:

```console
[root@node1 ~]# curl node1-pub:8080
Hostname: node1
IP: 127.0.0.1
IP: ::1
IP: 192.168.255.11
IP: fe80::30b6:61ff:feae:e86e
RemoteAddr: 192.168.121.67:42424
GET / HTTP/1.1
Host: node1-pub:8080
User-Agent: curl/8.0.1
Accept: */*
```

### Access from local host to `localhost`

This attempt fails:

<!-- file: demo1-ex4.sh -->
```sh
curl --connect-timeout 10 localhost:8080
```

Result:

```console
curl: (28) Failed to connect to localhost port 8080 after 10001 ms: Timeout was reached
```

Packets originating from `127.0.0.1` or `::1` are discarded by routing subsystem. We need to set `route_localnet` `sysctl` so that they are considered for routing:

<!-- file: demo1-ex4.sh -->
```sh
sysctl -w net.ipv4.conf.br0.route_localnet=1
```

The `curl` command still fails, because the packets arriving inside the namespace look like this:

```console
03:44:09.958193 IP 127.0.0.1.55054 > 192.168.255.11.80: Flags [S], seq 3086125734, win 65495, options [mss 65495,sackOK,TS val 4243937302 ecr 0,nop,wscale 7], length 0
```

We can't respond to a packet from `127.0.0.1`. We need a `MASQUERADE` rule for packets originating from `127.0.0.1`:

<!-- file: demo1-ex4.sh -->
```sh
iptables -t nat -A POSTROUTING -s 127.0.0.1 -d 192.168.255.0/24 -j MASQUERADE
```

Result:

```console
[root@node1 ~]# iptables -t nat -S
-P PREROUTING ACCEPT
-P INPUT ACCEPT
-P OUTPUT ACCEPT
-P POSTROUTING ACCEPT
-A PREROUTING -p tcp -m tcp --dport 8080 -j DNAT --to-destination 192.168.255.11:80
-A OUTPUT -p tcp -m tcp --dport 8080 -j DNAT --to-destination 192.168.255.11:80
-A POSTROUTING -s 192.168.255.0/24 -j MASQUERADE
-A POSTROUTING -s 127.0.0.1/32 -d 192.168.255.0/24 -j MASQUERADE
```

This allows the `curl` command to succeed:

```console
[root@node1 ~]# curl localhost:8080
Hostname: node1
IP: 127.0.0.1
IP: ::1
IP: 192.168.255.11
IP: fe80::30b6:61ff:feae:e86e
RemoteAddr: 192.168.255.1:52848
GET / HTTP/1.1
Host: localhost:8080
User-Agent: curl/8.0.1
Accept: */*
```

## Running a service in a namespace, take two

Goal: Show an alternate solution for handling traffic from `localhost`.

This is how Docker handles connections from the local host.

### Undo changes from previous example

Discard the `sysctl` setting and the `MASQUERADE` rule for traffic from `localhost`:

<!-- file: demo1-ex5.sh -->
```sh
sysctl -w net.ipv4.conf.br0.route_localnet=0
iptables -t nat -D POSTROUTING -s 127.0.0.1/32 -d 192.168.255.0/24 -j MASQUERADE
iptables -t nat -D OUTPUT -p tcp -m tcp --dport 8080 -j DNAT --to-destination 192.168.255.11:80
```

Result:

```console
[root@node1 ~]# iptables -t nat -S
-P PREROUTING ACCEPT
-P INPUT ACCEPT
-P OUTPUT ACCEPT
-P POSTROUTING ACCEPT
-A PREROUTING -p tcp -m tcp --dport 8080 -j DNAT --to-destination 192.168.255.11:80
-A POSTROUTING -s 192.168.255.0/24 -j MASQUERADE
```

### Configure a tcp proxy

<!-- file: demo1-ex5.sh -->
```sh
socat tcp-listen:8080,fork tcp-connect:192.168.255.11:80 &
```

Access to service from local host works:

```console
[root@node1 ~]# curl node1-pub:8080
Hostname: node1
IP: 127.0.0.1
IP: ::1
IP: 192.168.255.11
IP: fe80::30b6:61ff:feae:e86e
RemoteAddr: 192.168.255.1:41190
GET / HTTP/1.1
Host: node1-pub:8080
User-Agent: curl/8.0.1
Accept: */*

[root@node1 ~]# curl localhost:8080
Hostname: node1
IP: 127.0.0.1
IP: ::1
IP: 192.168.255.11
IP: fe80::30b6:61ff:feae:e86e
RemoteAddr: 192.168.255.1:46274
GET / HTTP/1.1
Host: localhost:8080
User-Agent: curl/8.0.1
Accept: */*
```
