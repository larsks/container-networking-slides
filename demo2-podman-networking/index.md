---
title: Podman container networking
---

## Containers on default bridge

<!-- file: demo2-ex1.sh -->

Goal: Understand how the network environment for a container closely resembles
what we built by hand in the previous demo.

### Examine network configuration

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
    inet 10.0.0.110/24 brd 10.0.0.255 scope global dynamic noprefixroute eth1
       valid_lft 3564sec preferred_lft 3564sec
    inet6 fe80::cd6a:6e22:6a43:a341/64 scope link noprefixroute
       valid_lft forever preferred_lft forever
```

### Create a container

```sh
podman run --rm --replace --name web1 --hostname web1 -d ghcr.io/larsks/whoami:main
```

Result:

```console
[root@node1 ~]# podman ps
CONTAINER ID  IMAGE                       COMMAND     CREATED        STATUS        PORTS       NAMES
5a6e9e0ccee7  ghcr.io/larsks/whoami:main  whoami      2 seconds ago  Up 2 seconds              web1
```

### Examine changes to network configuration

There's a new `podman0` bridge:

```sh
ip link show type bridge
ip link show master podman0
```

And a new namespace:

```sh
ip netns
```

Result:

```console
[root@node1 ~]# ip link show type bridge
4: podman0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default qlen 1000
    link/ether be:61:e0:f4:9f:e2 brd ff:ff:ff:ff:ff:ff
[root@node1 ~]# ip link show master podman0
5: veth0@if2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master podman0 state UP mode DEFAULT group default qlen 1000
    link/ether be:61:e0:f4:9f:e2 brd ff:ff:ff:ff:ff:ff link-netns netns-833f4c4b-c818-fc03-8bca-10c8f593fd9e
[root@node1 ~]# ip netns
netns-833f4c4b-c818-fc03-8bca-10c8f593fd9e (id: 0)
```

### Examine container network configuration

Using `podman exec`:

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

```sh
web1_pid=$(podman inspect web1 -f '{{.State.Pid}}')
nsenter -t $web1_pid -n ip addr
```

Result:

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

### Examine iptables rules

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
-N NETAVARK-HOSTPORT-DNAT
-N NETAVARK-HOSTPORT-MASQ
-N NETAVARK-HOSTPORT-SETMARK
-A PREROUTING -m addrtype --dst-type LOCAL -j NETAVARK-HOSTPORT-DNAT
-A OUTPUT -m addrtype --dst-type LOCAL -j NETAVARK-HOSTPORT-DNAT
-A POSTROUTING -j NETAVARK-HOSTPORT-MASQ
-A POSTROUTING -s 10.88.0.0/16 -j NETAVARK-1D8721804F16F
-A NETAVARK-1D8721804F16F -d 10.88.0.0/16 -j ACCEPT
-A NETAVARK-1D8721804F16F ! -d 224.0.0.0/4 -j MASQUERADE
-A NETAVARK-HOSTPORT-MASQ -m comment --comment "netavark portfw masq mark" -m mark --mark 0x2000/0x2000 -j MASQUERADE
-A NETAVARK-HOSTPORT-SETMARK -j MARK --set-xmark 0x2000/0x2000
```

## Default network vs user-defined network

<!-- file: demo2-ex2.sh -->

Goal: Show that DNS lookups work on user defined networks, but not on the
default network.

### Create two containers

```sh
podman run --rm --replace --name web1 --hostname web1 -d ghcr.io/larsks/whoami:main
podman run --rm --replace --name web2 --hostname web2 -d ghcr.io/larsks/whoami:main
```

Result:

```console
[root@node1 ~]# podman ps
CONTAINER ID  IMAGE                       COMMAND     CREATED        STATUS        PORTS       NAMES
26ecdb0cfd06  ghcr.io/larsks/whoami:main  whoami      3 seconds ago  Up 3 seconds              web1
85578efbceb5  ghcr.io/larsks/whoami:main  whoami      3 seconds ago  Up 3 seconds              web2
```

### Show name lookup failure

```sh
podman exec web1 curl -sS web2
```

Result:

```console
[root@node1 ~]# podman exec web1 curl -sS  web2
curl: (6) Could not resolve host: web2
```

### Create user-defined network

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

```sh
podman run --replace --name web1 --hostname web1 -d \
  --network mynetwork ghcr.io/larsks/whoami:main
podman run --replace --name web2 --hostname web2 -d \
  --network mynetwork ghcr.io/larsks/whoami:main
```

### Show name lookup success

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

## No published ports

<!-- file: demo2-ex3.sh -->

Goal: Understand how to access containerized services when we're not publishing
any ports.

### Start containers

```sh
podman run --rm --replace --name web1 --hostname web1 -d \
  --network mynetwork ghcr.io/larsks/whoami:main
podman run --rm --replace --name web2 --hostname web2 -d \
  --network mynetwork ghcr.io/larsks/whoami:main
```

### Demonstrate access from host

```sh
web1_addr=$(podman inspect web1 -f '{{.NetworkSettings.Networks.mynetwork.IPAddress}}')
curl $web1_addr
web2_addr=$(podman inspect web2 -f '{{.NetworkSettings.Networks.mynetwork.IPAddress}}')
curl $web2_addr
```

Result:

```console
[root@node1 ~]# web1_addr=$(podman inspect web1 -f '{{.NetworkSettings.Networks.mynetwork.IPAddress}}')
[root@node1 ~]# curl $web1_addr
Hostname: web1
IP: 127.0.0.1
IP: ::1
IP: 10.89.0.4
IP: fe80::e01f:95ff:fe05:6e63
RemoteAddr: 10.89.0.1:48756
GET / HTTP/1.1
Host: 10.89.0.4
User-Agent: curl/8.0.1
Accept: */*
[root@node1 ~]# web2_addr=$(podman inspect web2 -f '{{.NetworkSettings.Networks.mynetwork.IPAddress}}')
[root@node1 ~]# curl $web2_addr
Hostname: web2
IP: 127.0.0.1
IP: ::1
IP: 10.89.0.5
IP: fe80::4474:b4ff:fe28:178e
RemoteAddr: 10.89.0.1:60890
GET / HTTP/1.1
Host: 10.89.0.5
User-Agent: curl/8.0.1
Accept: */*
```

## Published on different ports

<!-- file: demo2-ex4.sh -->

Goal: Understand how to expose services on different host ports.

### Start containers

```sh
podman run --rm --replace --name web1 --hostname web1 -p 8080:80 -d \
  --network mynetwork ghcr.io/larsks/whoami:main
podman run --rm --replace --name web2 --hostname web2 -p 8081:80 -d \
  --network mynetwork ghcr.io/larsks/whoami:main
```

### Demonstrate access from host

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
-N NETAVARK-741C6CD328516
-N NETAVARK-DN-741C6CD328516
-N NETAVARK-HOSTPORT-DNAT
-N NETAVARK-HOSTPORT-MASQ
-N NETAVARK-HOSTPORT-SETMARK
-A PREROUTING -m addrtype --dst-type LOCAL -j NETAVARK-HOSTPORT-DNAT
-A OUTPUT -m addrtype --dst-type LOCAL -j NETAVARK-HOSTPORT-DNAT
-A POSTROUTING -j NETAVARK-HOSTPORT-MASQ
-A POSTROUTING -s 10.89.0.0/24 -j NETAVARK-741C6CD328516
-A NETAVARK-741C6CD328516 -d 10.89.0.0/24 -j ACCEPT
-A NETAVARK-741C6CD328516 ! -d 224.0.0.0/4 -j MASQUERADE
-A NETAVARK-DN-741C6CD328516 -s 10.89.0.0/24 -p tcp -m tcp --dport 8080 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-741C6CD328516 -s 127.0.0.1/32 -p tcp -m tcp --dport 8080 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-741C6CD328516 -p tcp -m tcp --dport 8080 -j DNAT --to-destination 10.89.0.6:80
-A NETAVARK-DN-741C6CD328516 -s 10.89.0.0/24 -p tcp -m tcp --dport 8081 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-741C6CD328516 -s 127.0.0.1/32 -p tcp -m tcp --dport 8081 -j NETAVARK-HOSTPORT-SETMARK
-A NETAVARK-DN-741C6CD328516 -p tcp -m tcp --dport 8081 -j DNAT --to-destination 10.89.0.7:80
-A NETAVARK-HOSTPORT-DNAT -p tcp -m tcp --dport 8080 -m comment --comment "dnat name: mynetwork id: d3795b1fd470ecf1f9f9cf649b377746b2ea435069594a36f096c833f89affe7" -j NETAVARK-DN-741C6CD328516
-A NETAVARK-HOSTPORT-DNAT -p tcp -m tcp --dport 8081 -m comment --comment "dnat name: mynetwork id: 72aac5fc11d8d4a6c49ccacd58ad5e01ef22ca76e05be606de01d3ad21bf8c90" -j NETAVARK-DN-741C6CD328516
-A NETAVARK-HOSTPORT-MASQ -m comment --comment "netavark portfw masq mark" -m mark --mark 0x2000/0x2000 -j MASQUERADE
-A NETAVARK-HOSTPORT-SETMARK -j MARK --set-xmark 0x2000/0x2000
```

## Published on different addresses

<!-- file: demo2-ex5.sh -->

Goal: Understand how to expose services on different host addresses.

### Configure additional addresses

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

```sh
podman run --rm --replace --name web1 --hostname web1 -p 192.168.121.200:80:80 -d \
  --network mynetwork ghcr.io/larsks/whoami:main
podman run --rm --replace --name web2 --hostname web2 -p 192.168.121.201:80:80 -d \
  --network mynetwork ghcr.io/larsks/whoami:main
```

Result:

```console
[root@node1 ~]# podman ps
CONTAINER ID  IMAGE                       COMMAND     CREATED        STATUS        PORTS                       NAMES
d8c01a597b12  ghcr.io/larsks/whoami:main  whoami      2 seconds ago  Up 2 seconds  192.168.121.200:80->80/tcp  web1
6af21b2fc41c  ghcr.io/larsks/whoami:main  whoami      1 second ago   Up 2 seconds  192.168.121.201:80->80/tcp  web2
```

### Confirm access from host

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
