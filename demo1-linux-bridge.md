---
title: Linux bridge device demo
---

The goal:

We will create two containers connected to the same virtual network. The
containers will be able to communicate with each other and will also be able to
access remote services.

## Create bridge

```
ip link add br0 type bridge
```

## Create namespaces

```
ip netns add ns1
ip netns add ns2
ip netns
```

## Create veth devices

```
ip link add vif1-int type veth peer name vif1-ext
ip link add vif2-int type veth peer name vif2-ext
ip link show type veth
```

## Assign vif devices to namespaces

```
ip link set netns ns1 dev vif1-int
ip link set netns ns2 dev vif2-int
ip netns exec ns1 ip addr
ip netns exec ns2 ip addr
ip link show type veth
```

## Add vif devices to bridge

```
ip link set master br0 dev vif1-ext
ip link set master br0 dev vif2-ext
ip link show master br0
```

## Assign addresses to internal interfaces

```
ip netns exec ns1 ip addr add 192.168.255.11/24 dev vif1-int
ip netns exec ns2 ip addr add 192.168.255.12/24 dev vif2-int
ip link set vif1-ext up
ip link set vif2-ext up
```

##  Show communication between containers

```
ip netns exec ns1 ping -c2 192.168.255.12
ip netns exec ns2 ping -c2 192.168.255.11
```

It didn't work! We need to bring everything up:

```
ip link set br0 up
ip link set vif1-ext up
ip link set vif2-ext up
ip netns exec ns1 ip link set vif1-int up
ip netns exec ns2 ip link set vif2-int up
```

## Show failure to communicate with host

```
HOSTADDR="$(ip addr show eth0 | awk '$1 == "inet" {print $2}' | cut -f1 -d/)"
ip netns exec ns1 ping -c2 $HOSTADDR
```

Run `tcpdump` on the host to show ICMP and ARP traffic.

## Add address to bridge

```
ip addr add 192.168.255.1/24 dev br0
```

## Add default route to namespaces

```
ip netns exec ns1 ip route add default via 192.168.255.1
ip netns exec ns2 ip route add default via 192.168.255.1
```

## Show successful communication with host

```
HOSTADDR="$(ip addr show eth0 | awk '$1 == "inet" {print $2}' | cut -f1 -d/)"
ip netns exec ns1 ping -c2 $HOSTADDR
```

## Show failure to communicate with external address

```
ip netns exec ns1 ping -c2 192.168.1.1
```

## Enable ip forwarding

```
sysctl -w net.ipv4.ip_forward=1
```

## Add masquerade rules on host

```
iptables -t nat -A POSTROUTING -s 192.168.255.0/24 -j MASQUERADE
```

## Show successful communication with external address

```
ip netns exec ns1 ping -c2 192.168.1.1
```
