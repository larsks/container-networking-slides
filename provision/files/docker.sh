# This configures Docker to talk to the root podman instance via the
# socket at /run/podman/podman.sock
export DOCKER_HOST=unix:///run/podman/podman.sock
