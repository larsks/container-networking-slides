# Debugging containers with nsenter

## Demonstrate tcpdump via nsenter

```
web1_pid=$(sudo podman inspect $(docker-compose ps -q web1) | jq -r '.[0].State.Pid')
sudo nsenter -t $web1_pid -n ip addr
sudo nsenter -t $web1_pid -n tcpdump -i eth0 -n
```

## Demonstrate tcpdump via ip netns

```
web1_netns=$(sudo podman inspect $(docker-compose ps -q web1) | jq -r '.[0].NetworkSettings.SandboxKey' | awk -F/ '{print $NF}')
ip netns exec $netns ip addr
ip netns exec $netns tcpdump -i eth0 -n
```

