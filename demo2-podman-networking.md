---
title: Podman container networking
---

## Containers on default bridge

Goal: Understand how the network environment for a container closely resembles
what we built by hand in the previous demo.

### Examine network configuration

```
ip addr
```

### Create a container

```
podman run --name web1 -d quay.io/larsks/nginx-cnd:latest
```

### Examine changes to network configuration

There's a new `cni-podman0` bridge:

```
ip link show type bridge
ip link show master cni-podman0
```

And a new namespace:

```
ip netns
```

### Examine container network configuration

Using `podman exec`:

```
podman exec web1 ip addr
```

Using `nsenter`:

```
web1_pid=$(podman inspect web1 | jq '.[0].State.Pid')
nsenter -t $web1_pid -n ip addr
nsenter -t $web1_pid -n ip route
```

### Examine iptables rules

```
iptables -t nat -S
```

## Default network vs user-defined network

Goal: Show that DNS lookups work on user defined networks, but not on the
default network.

### Create two containers

```
podman run --name web1 --hostname web1 -d quay.io/larsks/nginx-cnd:latest
podman run --name web2 --hostname web2 -d quay.io/larsks/nginx-cnd:latest
```

### Show name lookup failure

```
podman exec web1 curl web2
```

### Create user-defined network

```
podman network create mynetwork
```

### Create containers attached to network

```
podman run --name web1 --hostname web1 -d --network mynetwork quay.io/larsks/nginx-cnd:latest
podman run --name web2 --hostname web2 -d --network mynetwork quay.io/larsks/nginx-cnd:latest
```

### Show name lookup success

```
podman exec web1 curl web2
```

## No published ports

Goal: Understand how to access containerized services when we're not publishing
any ports.

### Start containers

```
podman run --name web1 --hostname web1 -d --network mynetwork quay.io/larsks/nginx-cnd:latest
podman run --name web2 --hostname web2 -d --network mynetwork quay.io/larsks/nginx-cnd:latest
```

### Demonstrate access from host

```
web1_addr=$(podman inspect web1 | jq -r '.[0].NetworkSettings.Networks.mynetwork.IPAddress')
curl $web1_addr
```

## Published on different ports

Goal: Understand how to expose services on different host ports.

### Start containers

```
podman run --name web1 --hostname web1 -p 8080:80 -d --network mynetwork quay.io/larsks/nginx-cnd:latest
podman run --name web2 --hostname web2 -p 8081:80 -d --network mynetwork quay.io/larsks/nginx-cnd:latest
```

### Demonstrate access from host

- http://node1.local:8080
- http://node1.local:8081

## Published on different addresses

Goal: Understand how to expose services on different host addresses.

### Configure additional addresses

```
ip addr add 192.168.121.200/24 dev eth0
ip addr add 192.168.121.201/24 dev eth0
```

### Start containers

```
podman run --name web1 --hostname web1 -p 192.168.121.200:80:80 -d --network mynetwork quay.io/larsks/nginx-cnd:latest
podman run --name web2 --hostname web2 -p 192.168.121.201:80:80 -d --network mynetwork quay.io/larsks/nginx-cnd:latest
```

### Confirm access from host

- http://192.168.121.200
- http://192.168.121.201
