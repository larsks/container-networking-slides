# vim: set ft=ruby:

Vagrant.configure("2") do |config|
  node_count=2

  config.vm.provider :libvirt do |libvirt|
    libvirt.uri = "qemu:///system"
    libvirt.memory = 4096
  end

  config.vm.box = "fedora/35-cloud-base"
  config.vm.box_version = "35.20211026.0"

  (1..node_count).each do |machine_id|
    config.vm.define "node#{machine_id}" do |node|
      node.vm.hostname = "node#{machine_id}"
      node.vm.network :private_network,
        :forward_mode => "open",
        :ip => "10.0.0.#{10 + machine_id}",
        :libvirt_netmask => "255.255.255.0"
      node.vm.provider :libvirt do |libvirt|
        libvirt.storage :file,
          :size => "10G",
          :type => "qcow2"
      end
    end
  end

  config.vm.provision :ansible do |ansible|
    ansible.compatibility_mode = "2.0"
    ansible.playbook = "provision.yml"
    ansible.groups = {
      "nodes" => Array.new(node_count) { |machine_id| "node#{machine_id+1}" },
    }
  end
end
