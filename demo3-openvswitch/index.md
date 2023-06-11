---
title: OpenVSwitch networking demo
nav_order: 3
---

* Table of contents
{:toc}

## Connect two containers

Goal: Attach two containers to an OVS bridge and demonstrate successful communication.

### Create OVS bridge

<!-- file: demo3-ex1.sh -->
```sh
ovs-vsctl add-br br1
ip link set br1 up
```

Result:

```console
[root@node1 ~]# ovs-vsctl show
e2569579-f87a-4cd9-8d2c-e734a8849301
    Bridge br1
        Port br1
            Interface br1
                type: internal
    ovs_version: "3.1.1"
[root@node1 ~]# ip link show br1
5: br1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/ether a2:e5:df:9b:05:40 brd ff:ff:ff:ff:ff:ff
```

### Create namespaces

<!-- file: demo3-ex1.sh -->
```sh
ip netns add ns1
ip netns add ns2
```

### Create internal ports

<!-- file: demo3-ex1.sh -->
```sh
ovs-vsctl add-port br1 vif1 -- set interface vif1 type=internal
ovs-vsctl add-port br1 vif2 -- set interface vif2 type=internal
```

Result:

```console
[root@node1 ~]# ovs-vsctl show
f151beb1-81eb-44b7-ab78-94524aae8bc8
    Bridge br1
        Port vif1
            Interface vif1
                type: internal
        Port br1
            Interface br1
                type: internal
        Port vif2
            Interface vif2
                type: internal
    ovs_version: "3.1.1"
[root@node1 ~]# ip link show
...
4: ovs-system: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether 76:42:22:37:08:ad brd ff:ff:ff:ff:ff:ff
5: br1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/ether a2:e5:df:9b:05:40 brd ff:ff:ff:ff:ff:ff
6: vif1: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether 5a:e4:e3:74:0b:65 brd ff:ff:ff:ff:ff:ff
7: vif2: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether fa:dd:b8:f3:a1:85 brd ff:ff:ff:ff:ff:ff
```

### Assign internal ports to namespaces

<!-- file: demo3-ex1.sh -->
```sh
ip link set netns ns1 dev vif1
ip link set netns ns2 dev vif2
```

### Assign addresses to internal interfaces

<!-- file: demo3-ex1.sh -->
```sh
ip -n ns1 addr add 192.168.255.11/24 dev vif1
ip -n ns1 link set vif1 up
ip -n ns1 link set lo up
ip -n ns2 addr add 192.168.255.12/24 dev vif2
ip -n ns2 link set vif2 up
ip -n ns2 link set lo up
```

###  Show communication between containers

<!-- file: demo3-ex1.sh -->
```sh
ip netns exec ns1 ping -c2 192.168.255.12
ip netns exec ns2 ping -c2 192.168.255.11
```

## Overlay networking

Goal: Make containers on multiple hosts appear on the same internal network. We will use [Geneve][] tunnels to create a virtual network across two hosts.

[geneve]: https://en.wikipedia.org/wiki/Generic_Network_Virtualization_Encapsulation

### Create OVS bridge

On `node2` run:

<!-- file: demo3-ex2-node2.sh -->
```sh
ovs-vsctl add-br br1
ip link set br1 up
```

### Create namespaces

On `node2` run:

<!-- file: demo3-ex2-node2.sh -->
```sh
ip netns add ns3
```

### Create internal ports

On `node2` run:

<!-- file: demo3-ex2-node2.sh -->
```sh
ovs-vsctl add-port br1 vif3 -- set interface vif3 type=internal
```

### Assign internal ports to namespaces

On `node2` run:

<!-- file: demo3-ex2-node2.sh -->
```sh
ip link set netns ns3 dev vif3
```

### Assign addresses to internal interfaces

On `node2` run:

<!-- file: demo3-ex2-node2.sh -->
```sh
ip -n ns3 addr add 192.168.255.13/24 dev vif3
ip -n ns3 link set vif3 up
```

### Create geneve port (node2)

On `node2` run:

<!-- file: demo3-ex2-node2.sh -->
```sh
NODE1_ADDR=$(getent hosts node1-pvt | awk '{print $1}')
ovs-vsctl add-port br1 tun1 -- set interface tun1 \
  type=geneve options:remote_ip=$NODE1_ADDR
```

Result:

```console
[root@node2 ~]# ovs-vsctl show
d4e01762-4cd1-4e53-b502-78f852cd1ad3
    Bridge br1
        Port br1
            Interface br1
                type: internal
        Port tun1
            Interface tun1
                type: geneve
                options: {remote_ip="10.0.0.110"}
        Port vif3
            Interface vif3
                type: internal
    ovs_version: "3.1.1"
```

### Create geneve port (node1)

On `node1` run:

<!-- file: demo3-ex2-node1.sh -->
```sh
NODE2_ADDR=$(getent hosts node2-pvt | awk '{print $1}')
ovs-vsctl add-port br1 tun1 -- set interface tun1 \
  type=geneve options:remote_ip=$NODE2_ADDR
```

Result:

```console
[root@node1 ~]# ovs-vsctl show
f151beb1-81eb-44b7-ab78-94524aae8bc8
    Bridge br1
        Port vif1
            Interface vif1
                type: internal
        Port br1
            Interface br1
                type: internal
        Port tun1
            Interface tun1
                type: geneve
                options: {remote_ip="10.0.0.23"}
        Port vif2
            Interface vif2
                type: internal
    ovs_version: "3.1.1"
```

### Show successful communication with ns3

Namespaces on `node1` can reach namespaces on `node2`:

```console
[root@node1 ~]# ip netns exec ns1 ping -c2 192.168.255.13
PING 192.168.255.13 (192.168.255.13) 56(84) bytes of data.
64 bytes from 192.168.255.13: icmp_seq=1 ttl=64 time=0.901 ms
64 bytes from 192.168.255.13: icmp_seq=2 ttl=64 time=0.437 ms

--- 192.168.255.13 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1051ms
rtt min/avg/max/mdev = 0.437/0.669/0.901/0.232 ms
```

Namespaces on `node2` can reach namespaces on `node1`:

```console
[root@node2 ~]# ip netns exec ns3 ping -c2 192.168.255.11
PING 192.168.255.11 (192.168.255.11) 56(84) bytes of data.
64 bytes from 192.168.255.11: icmp_seq=1 ttl=64 time=0.627 ms
64 bytes from 192.168.255.11: icmp_seq=2 ttl=64 time=0.343 ms

--- 192.168.255.11 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1054ms
rtt min/avg/max/mdev = 0.343/0.485/0.627/0.142 ms
```

## Outbound access through node1

Goal: Configure access to remote networks. Demonstrate that `ns3` accesses
remote networks through the bridge on `node1`.

### Add default route to `ns3`

On `node1` run:

<!-- file: demo3-ex3-node1.sh -->
```sh
ip -n ns1 route add default via 192.168.255.1
ip -n ns2 route add default via 192.168.255.1
```

On `node2` run:

<!-- file: demo3-ex3-node2.sh -->
```sh
ip -n ns3 route add default via 192.168.255.1
```

### Add gateway address to OVS bridge

On `node1` run:

<!-- file: demo3-ex3-node1.sh -->
```sh
ip addr add 192.168.255.1/24 dev br1
```

### Enable ip forwarding

On `node1` run:

<!-- file: demo3-ex3-node1.sh -->
```sh
sysctl -w net.ipv4.ip_forward=1
```

### Add masquerade rule

On `node1` run:

<!-- file: demo3-ex3-node1.sh -->
```sh
iptables -t nat -A POSTROUTING -s 192.168.255.0/24 -j MASQUERADE
```

### Show successful communication with remote address

Namespace `ns3` on `node2` can reach remote sites via the default gateway on `node1`:

```console
[root@node2 ~]# ip netns exec ns3 ping -c2 8.8.8.8
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=115 time=12.9 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=115 time=11.3 ms

--- 8.8.8.8 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1001ms
rtt min/avg/max/mdev = 11.291/12.105/12.919/0.814 ms
```

Use `tcpdump` on `node1` to show traffic. See encapsulated traffic on `eth1`:

```console
[root@node1 ~]# tcpdump -i eth1 -nn not broadcast and not multicast
dropped privs to tcpdump
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on eth1, link-type EN10MB (Ethernet), snapshot length 262144 bytes
18:45:33.653282 IP 10.0.0.23.63032 > 10.0.0.110.6081: Geneve, Flags [none], vni 0x0: IP 192.168.255.13 > 8.8.8.8: ICMP echo request, id 10039, seq 1, length 64
18:45:33.666858 IP 10.0.0.110.55384 > 10.0.0.23.6081: Geneve, Flags [none], vni 0x0: IP 8.8.8.8 > 192.168.255.13: ICMP echo reply, id 10039, seq 1, length 64
18:45:34.654735 IP 10.0.0.23.63032 > 10.0.0.110.6081: Geneve, Flags [none], vni 0x0: IP 192.168.255.13 > 8.8.8.8: ICMP echo request, id 10039, seq 2, length 64
18:45:34.670627 IP 10.0.0.110.55384 > 10.0.0.23.6081: Geneve, Flags [none], vni 0x0: IP 8.8.8.8 > 192.168.255.13: ICMP echo reply, id 10039, seq 2, length 64
```

And the un-encapsulated traffic egressing on `eth0`:

```console
[root@node1 ~]# tcpdump -i eth0 -nn  icmp
dropped privs to tcpdump
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on eth0, link-type EN10MB (Ethernet), snapshot length 262144 bytes
18:47:00.197273 IP 192.168.121.67 > 8.8.8.8: ICMP echo request, id 43434, seq 1, length 64
18:47:00.210539 IP 8.8.8.8 > 192.168.121.67: ICMP echo reply, id 43434, seq 1, length 64
18:47:01.198340 IP 192.168.121.67 > 8.8.8.8: ICMP echo request, id 43434, seq 2, length 64
18:47:01.211751 IP 8.8.8.8 > 192.168.121.67: ICMP echo reply, id 43434, seq 2, length 64
```
