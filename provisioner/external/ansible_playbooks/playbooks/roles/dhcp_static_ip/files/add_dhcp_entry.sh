#!/bin/bash

# Title         Add a DHCP static IP entry
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux & macOS
# Description   Define a static IP on the DHCP clietn deamon
#==============================================================================
verify_dhcpcd_is_running() {
  local dhcpcd_exists=$(systemctl list-units --full -all | grep -i "dhcpcd.service")
  if [[ -z "${dhcpcd_exists}" ]]; then
    echo "Cannot find mandatory DHCP client daemon service. name: dhcpcd.service"
    exit 1
  else
    echo "Found DHCP client daemon service. name: dhcpcd.service"
  fi

  local status=$(systemctl show -p SubState dhcpcd)
  if [[ "${status}" != *"running"* ]]; then
    echo "DHCP client daemon is not running, starting service..."
    systemctl start dhcpcd
  else
    echo "DHCP client daemon is running"
  fi

  local active_state=$(systemctl show -p ActiveState dhcpcd)
  if [[ "${active_state}" != *"active"* ]]; then
    echo "DHCP client daemon is not set as active, activating service..."
    systemctl enable dhcpcd
  else
    echo "DHCP client daemon is enabled"
  fi
}

configure_static_ip_address() {
  local eth0_static_ip_section="
interface eth0
static ip_address=${ENV_STATIC_IP}/24
static routers=${ENV_GATEWAY_ADDRESS}
static domain_name_servers=${ENV_DNS_ADDRESS}
"

  if grep -q -w "ip_address=${ENV_STATIC_IP}" "/etc/dhcpcd.conf"; then
    echo "Entry '${ENV_STATIC_IP}' already exists in /etc/dhcpcd.conf"
  else
    echo "Updating DHCP client daemon config file. path: /etc/dhcpcd.conf"
    printf "${eth0_static_ip_section}" >> /etc/dhcpcd.conf
#    touch /tmp/test.conf
#    printf "${eth0_static_ip_section}" >> /tmp/test.conf
  fi
}

verify_mandatory_variables() {
  if [[ -z "${ENV_STATIC_IP}" ]]; then
      echo "missing mandatory argument. name: static_ip"
      exit 1
  fi

  if [[ -z "${ENV_GATEWAY_ADDRESS}" ]]; then
      echo "missing mandatory argument. name: gateway_address"
      exit 1
  fi

  if [[ -z "${ENV_DNS_ADDRESS}" ]]; then
      echo "missing mandatory argument. name: dns_address"
      exit 1
  fi
}

main() {
  verify_dhcpcd_is_running
  configure_static_ip_address
}

main "$@"