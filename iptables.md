# Podman iptables

## No port forwarding

Outbound packet:

```
-A POSTROUTING -m comment --comment "CNI portfwd requiring masquerade" -j CNI-HOSTPORT-MASQ
-A POSTROUTING -m comment --comment "CNI portfwd requiring masquerade" -j CNI-HOSTPORT-MASQ
-A POSTROUTING -s 10.89.0.9/32 -m comment --comment "name: \"demo31_default\" id: \"b2644dfd47b74eec3f943fd472fd91f1cc5ef0e9a0c78510f12aa2dae7893d67\"" -j CNI-da496b9a098ae9e1e87cd049
-A POSTROUTING -s 10.89.0.8/32 -m comment --comment "name: \"demo31_default\" id: \"9cd32bdc900f895137acfb9b6f314650c1c5d20a57e6ce8113dd5fcf9de0865b\"" -j CNI-be3a24ea7b0f6a3dcf2e2adf

-A CNI-HOSTPORT-MASQ -m mark --mark 0x2000/0x2000 -j MASQUERADE

-A CNI-be3a24ea7b0f6a3dcf2e2adf -d 10.89.0.0/24 -m comment --comment "name: \"demo31_default\" id: \"9cd32bdc900f895137acfb9b6f314650c1c5d20a57e6ce8113dd5fcf9de0865b\"" -j ACCEPT
-A CNI-be3a24ea7b0f6a3dcf2e2adf ! -d 224.0.0.0/4 -m comment --comment "name: \"demo31_default\" id: \"9cd32bdc900f895137acfb9b6f314650c1c5d20a57e6ce8113dd5fcf9de0865b\"" -j MASQUERADE
-A CNI-da496b9a098ae9e1e87cd049 -d 10.89.0.0/24 -m comment --comment "name: \"demo31_default\" id: \"b2644dfd47b74eec3f943fd472fd91f1cc5ef0e9a0c78510f12aa2dae7893d67\"" -j ACCEPT
-A CNI-da496b9a098ae9e1e87cd049 ! -d 224.0.0.0/4 -m comment --comment "name: \"demo31_default\" id: \"b2644dfd47b74eec3f943fd472fd91f1cc5ef0e9a0c78510f12aa2dae7893d67\"" -j MASQUERADE
```

## With port forwarding

Inbound packet:

```
-A PREROUTING -m addrtype --dst-type LOCAL -j CNI-HOSTPORT-DNAT

-A CNI-HOSTPORT-DNAT -p tcp -m comment --comment "dnat name: \"demo32_default\" id: \"3d1b765e160807e6cef638a0f0df6f6238cb62f64149f212cacd4d1ff6ad40cf\"" -m multiport --dports 8081 -j CNI-DN-4b4398da9cebdf54f85fe
-A CNI-HOSTPORT-DNAT -p tcp -m comment --comment "dnat name: \"demo32_default\" id: \"0faf68d181aed164bb03495f3a939818cddeb8ecb8c8a1d06ed9805cc378ef4a\"" -m multiport --dports 8080 -j CNI-DN-95712aea8e190735cbde3

-A CNI-DN-4b4398da9cebdf54f85fe -s 10.89.0.0/24 -p tcp -m tcp --dport 8081 -j CNI-HOSTPORT-SETMARK
-A CNI-DN-4b4398da9cebdf54f85fe -s 127.0.0.1/32 -p tcp -m tcp --dport 8081 -j CNI-HOSTPORT-SETMARK
-A CNI-DN-4b4398da9cebdf54f85fe -p tcp -m tcp --dport 8081 -j DNAT --to-destination 10.89.0.2:80
-A CNI-DN-95712aea8e190735cbde3 -s 10.89.0.0/24 -p tcp -m tcp --dport 8080 -j CNI-HOSTPORT-SETMARK
-A CNI-DN-95712aea8e190735cbde3 -s 127.0.0.1/32 -p tcp -m tcp --dport 8080 -j CNI-HOSTPORT-SETMARK
-A CNI-DN-95712aea8e190735cbde3 -p tcp -m tcp --dport 8080 -j DNAT --to-destination 10.89.0.3:80
```

Outbound packet:

```
-A POSTROUTING -m comment --comment "CNI portfwd requiring masquerade" -j CNI-HOSTPORT-MASQ
-A POSTROUTING -s 10.89.0.2/32 -m comment --comment "name: \"demo32_default\" id: \"3d1b765e160807e6cef638a0f0df6f6238cb62f64149f212cacd4d1ff6ad40cf\"" -j CNI-4b4398da9cebdf54f85feefc
-A POSTROUTING -s 10.89.0.3/32 -m comment --comment "name: \"demo32_default\" id: \"0faf68d181aed164bb03495f3a939818cddeb8ecb8c8a1d06ed9805cc378ef4a\"" -j CNI-95712aea8e190735cbde37f7

-A CNI-HOSTPORT-MASQ -m mark --mark 0x2000/0x2000 -j MASQUERADE

-A CNI-4b4398da9cebdf54f85feefc -d 10.89.0.0/24 -m comment --comment "name: \"demo32_default\" id: \"3d1b765e160807e6cef638a0f0df6f6238cb62f64149f212cacd4d1ff6ad40cf\"" -j ACCEPT
-A CNI-4b4398da9cebdf54f85feefc ! -d 224.0.0.0/4 -m comment --comment "name: \"demo32_default\" id: \"3d1b765e160807e6cef638a0f0df6f6238cb62f64149f212cacd4d1ff6ad40cf\"" -j MASQUERADE
-A CNI-95712aea8e190735cbde37f7 -d 10.89.0.0/24 -m comment --comment "name: \"demo32_default\" id: \"0faf68d181aed164bb03495f3a939818cddeb8ecb8c8a1d06ed9805cc378ef4a\"" -j ACCEPT
-A CNI-95712aea8e190735cbde37f7 ! -d 224.0.0.0/4 -m comment --comment "name: \"demo32_default\" id: \"0faf68d181aed164bb03495f3a939818cddeb8ecb8c8a1d06ed9805cc378ef4a\"" -j MASQUERADE
```

## Published on different addressess

```
-P PREROUTING ACCEPT
-P INPUT ACCEPT
-P OUTPUT ACCEPT
-P POSTROUTING ACCEPT
-N CNI-267ec35d0ab912bcb67831e4
-N CNI-9a64705d83cfdacfbcd48dc2
-N CNI-DN-267ec35d0ab912bcb6783
-N CNI-DN-9a64705d83cfdacfbcd48
-N CNI-HOSTPORT-DNAT
-N CNI-HOSTPORT-MASQ
-N CNI-HOSTPORT-SETMARK
-A PREROUTING -m addrtype --dst-type LOCAL -j CNI-HOSTPORT-DNAT
-A OUTPUT -m addrtype --dst-type LOCAL -j CNI-HOSTPORT-DNAT
-A POSTROUTING -m comment --comment "CNI portfwd requiring masquerade" -j CNI-HOSTPORT-MASQ
-A POSTROUTING -s 10.89.0.3/32 -m comment --comment "name: \"demo33_default\" id: \"cc97b819128549e7afe0f1d2747524f2338ffdcba9fd8c44973129b0047f2d24\"" -j CNI-9a64705d83cfdacfbcd48dc2
-A POSTROUTING -s 10.89.0.2/32 -m comment --comment "name: \"demo33_default\" id: \"97e2e73c1be36459124aef74a474e13a44c7ce8e2426d48f844540673d05ffd1\"" -j CNI-267ec35d0ab912bcb67831e4
-A CNI-267ec35d0ab912bcb67831e4 -d 10.89.0.0/24 -m comment --comment "name: \"demo33_default\" id: \"97e2e73c1be36459124aef74a474e13a44c7ce8e2426d48f844540673d05ffd1\"" -j ACCEPT
-A CNI-267ec35d0ab912bcb67831e4 ! -d 224.0.0.0/4 -m comment --comment "name: \"demo33_default\" id: \"97e2e73c1be36459124aef74a474e13a44c7ce8e2426d48f844540673d05ffd1\"" -j MASQUERADE
-A CNI-9a64705d83cfdacfbcd48dc2 -d 10.89.0.0/24 -m comment --comment "name: \"demo33_default\" id: \"cc97b819128549e7afe0f1d2747524f2338ffdcba9fd8c44973129b0047f2d24\"" -j ACCEPT
-A CNI-9a64705d83cfdacfbcd48dc2 ! -d 224.0.0.0/4 -m comment --comment "name: \"demo33_default\" id: \"cc97b819128549e7afe0f1d2747524f2338ffdcba9fd8c44973129b0047f2d24\"" -j MASQUERADE
-A CNI-DN-267ec35d0ab912bcb6783 -s 10.89.0.0/24 -d 192.168.121.201/32 -p tcp -m tcp --dport 80 -j CNI-HOSTPORT-SETMARK
-A CNI-DN-267ec35d0ab912bcb6783 -s 127.0.0.1/32 -d 192.168.121.201/32 -p tcp -m tcp --dport 80 -j CNI-HOSTPORT-SETMARK
-A CNI-DN-267ec35d0ab912bcb6783 -d 192.168.121.201/32 -p tcp -m tcp --dport 80 -j DNAT --to-destination 10.89.0.2:80
-A CNI-DN-9a64705d83cfdacfbcd48 -s 10.89.0.0/24 -d 192.168.121.200/32 -p tcp -m tcp --dport 80 -j CNI-HOSTPORT-SETMARK
-A CNI-DN-9a64705d83cfdacfbcd48 -s 127.0.0.1/32 -d 192.168.121.200/32 -p tcp -m tcp --dport 80 -j CNI-HOSTPORT-SETMARK
-A CNI-DN-9a64705d83cfdacfbcd48 -d 192.168.121.200/32 -p tcp -m tcp --dport 80 -j DNAT --to-destination 10.89.0.3:80
-A CNI-HOSTPORT-DNAT -p tcp -m comment --comment "dnat name: \"demo33_default\" id: \"cc97b819128549e7afe0f1d2747524f2338ffdcba9fd8c44973129b0047f2d24\"" -m multiport --dports 80 -j CNI-DN-9a64705d83cfdacfbcd48
-A CNI-HOSTPORT-DNAT -p tcp -m comment --comment "dnat name: \"demo33_default\" id: \"97e2e73c1be36459124aef74a474e13a44c7ce8e2426d48f844540673d05ffd1\"" -m multiport --dports 80 -j CNI-DN-267ec35d0ab912bcb6783
-A CNI-HOSTPORT-MASQ -m mark --mark 0x2000/0x2000 -j MASQUERADE
-A CNI-HOSTPORT-SETMARK -m comment --comment "CNI portfwd masquerade mark" -j MARK --set-xmark 0x2000/0x2000
```
