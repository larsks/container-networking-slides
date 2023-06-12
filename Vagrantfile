# vim: set ft=ruby:

Vagrant.configure("2") do |config|
  node_count=2

  config.vm.provider :libvirt do |libvirt|
    libvirt.uri = "qemu:///system"
    libvirt.memory = 4096
    libvirt.storage :file, :size => "10G", :type => "qcow2"
  end

  config.vm.box = "fedora/38-cloud-base"

  (1..node_count).each do |machine_id|
    config.vm.define "node#{machine_id}" do |node|
      node.vm.hostname = "node#{machine_id}"
      node.vm.network :private_network,
        :ip => "10.0.0.#{10 + machine_id}"

      if machine_id == node_count
        node.vm.provision :ansible do |ansible|
          ansible.limit = "all"
          ansible.playbook = "provision.yaml"
        end
      end
    end

  end
end
