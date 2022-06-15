# Open vSwitch demo

## On node1

### Create bridge

```
ovs-vsctl add-br br1
ip link set br1 up
ovs-vsctl show
```

### Create namespaces

```
ip netns add ns1
ip netns add ns2
ip netns
```

### Create internal ports

```
ovs-vsctl add-port br1 vif1 -- set interface vif1 type=internal
ovs-vsctl add-port br1 vif2 -- set interface vif2 type=internal
ovs-vsctl show
```

### Assign internal ports to namespaces

```
ip link set netns ns1 dev vif1
ip link set netns ns2 dev vif2
```

### Assign addresses to internal interfaces

```
ip netns exec ns1 ip addr add 192.168.255.11/24 dev vif1
ip netns exec ns1 ip link set vif1 up
ip netns exec ns2 ip addr add 192.168.255.12/24 dev vif2
ip netns exec ns2 ip link set vif2 up
```

###  Show communication between containers

```
ip netns exec ns1 ping -c2 192.168.255.12
ip netns exec ns2 ping -c2 192.168.255.11
```

### Add default route to namespaces

```
ip netns exec ns1 ip route add default via 192.168.255.1
ip netns exec ns2 ip route add default via 192.168.255.1
```


### Enable ip forwarding

```
sysctl -w net.ipv4.ip_forward=1
```

### Add masquerade rules on host

```
iptables -t nat -A POSTROUTING -s 192.168.255.0/24 -j MASQUERADE
```

### Add address to bridge

```
ip addr add 192.168.255.1/24 dev br1
```

## Show successful communication with external address

```
ip netns exec ns1 ping -c2 192.168.1.1
```

## On node2

### Create bridge

```
ovs-vsctl add-br br1
ip link set br1 up
ovs-vsctl show
```

### Create namespaces

```
ip netns add ns3
ip netns
```

### Create internal ports

```
ovs-vsctl add-port br1 vif3 -- set interface vif3 type=internal
ovs-vsctl show
```

### Assign internal ports to namespaces

```
ip link set netns ns3 dev vif3
```

### Assign addresses to internal interfaces

```
ip netns exec ns3 ip addr add 192.168.255.13/24 dev vif3
ip netns exec ns3 ip link set vif3 up
```

### Create vxlan port

```
NODE1_ADDR=$(getent hosts node1.local | awk '{print $1}')
ovs-vsctl add-port br1 tun1 -- set interface tun1 \
  type=vxlan options:remote_ip=$NODE1_ADDR
```

## On node1

### Create vxlan port

```
NODE2_ADDR=$(getent hosts node2.local | awk '{print $1}')
ovs-vsctl add-port br1 tun1 -- set interface tun1 \
  type=vxlan options:remote_ip=$NODE2_ADDR
```

### Show successful communication with ns3

```
ip netns exec ns1 ping -c2 192.168.255.13
```

## On node2

### Add default route to namespace

```
ip netns exec ns3 ip route add default via 192.168.255.1
```

### Show successful communication with external address

```
ip netns exec ns3 ping -c2 192.168.1.1
```

