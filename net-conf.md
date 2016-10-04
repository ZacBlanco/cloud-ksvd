# Cluster Network Configuration

The purpose of this file is to describe the cluster network configuration that was used to test this implementation of Cloud K-SVD

## Network Description

There are 5 nodes (raspberry pi's) in our cluster. Each node is connected via a WiFi antenna to the same 2.4GHz network. The network has anywhere from 0-12 Users at a time with each user having anywhere from 1-5 devices. This works out to a maximum of 60+5 devices using the same wireless network at a single time.

The network topology of the five nodes can be represented by a complete graph wherein each node can communicate with any other node in the graph topology, or the node itself.

The reason we do this is so that we can simply manipulate the graph topology of the algorithm while running, rather than having to change the software or hardware configuration directly in the testing environment.

However challenges do arise if we want to try do large-scaled testing across multiple graphically distributed regions. Where we might run into other issues where we can't test an entirely connected graph. 

## Hardware Description

On the hardware the nodes are labeled: A, B, C, D, E. Each node also has its own antenna labeled A, B, C, and D in order to make sure the performance among nodes will not change if the hardware is ever reconfigured.

The power draw of the antennas is something that has yet to be investigated, but it has been found so far that none of the pi's necessarily require a powered hub for the antenna, however we investigate if a separately powered antenna improves performance.

All of the nodes run the following hardware:

- Raspberry Pi Model B+ Board
- 5V 2000mA DC power supply
- LB-Link 155A Wireless N USB2.0 WiFi adapter.

In the case where we use a powered hub:

- Manhattan 7-Port Wired USB2.0 Hub

## Software Configuration

All of the nodes have SSH servers so direct connections to monitors and peripherals are not necessary.

Each node is configured on the 2.4GHz Wireless network with a static IP and hostname according to the following table.

| Pi Hardware Label | Static Network IP | hostname      |
|-------------------|-------------------|---------------|
| A                 | 192.168.1.180     | jared.siv     |
| B                 | 192.168.1.181     | bighead.siv   |
| C                 | 192.168.1.182     | gilfoyle.siv  |
| D                 | 192.168.1.183     | dinesh.siv    |
| E                 | 192.168.1.184     | erlich.siv    |

\* = still the default raspbian hostname. Has not been setup yet.

### Sample `/etc/network/interfaces` File

```configuration
# interfaces(5) file used by ifup(8) and ifdown(8)

# Please note that this file is written to be used with dhcpcd
# For static IP, consult /etc/dhcpcd.conf and 'man dhcpcd.conf'

# Include files from /etc/network/interfaces.d:
source-directory /etc/network/interfaces.d

#auto lo
#iface lo inet loopback

#iface eth0 inet manual

#allow-hotplug wlan0
#iface wlan0 inet manual
#    wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf

#allow-hotplug wlan1
#iface wlan1 inet manual
#    wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf

auto lo

iface lo inet loopback
iface eth0 inet manual

allow-hotplug wlan0
auto wlan0

iface wlan0 inet static
        wpa-ssid "NETWORK_SSID"
        wpa-psk "NET_PASSWORD"
        address 192.168.1.180
        gateway 192.168.1.1
        netmask 255.255.255.0
        network 192.168.1.0
        broadcast 192.168.1.255
```

And also here's a an `/etc/hosts` file that you can use to resolve the local IP's of the pi's via hostnames instead of IP addresses.

Distribute this file to your own computer and all of the nodes in the network for easy hostname resolution.

```conf
127.0.0.1 localhost
::1             localhost ip6-localhost ip6-loopback
ff02::1         ip6-allnodes
ff02::2         ip6-allrouters

192.168.1.180 jared.siv
192.168.1.181 bighead.siv
192.168.1.182 gilfoyle.siv
192.168.1.183 dinesh.siv
192.168.1.184 erlich.siv
```






