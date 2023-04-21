"""Module for detecting my VPN client.

This will be of limited use to other people, and should be rethought entirely before open sourceing.
"""
import psutil
import socket

VPN_INTERFACE_PREFIX = "utun"
IP_PREFIX = "172.29"


def is_vpn_connected() -> bool:
    interfaces = psutil.net_if_addrs()

    for interface, addrs in interfaces.items():
        if interface.startswith(VPN_INTERFACE_PREFIX):
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address.startswith(IP_PREFIX):
                    return True

    return False
