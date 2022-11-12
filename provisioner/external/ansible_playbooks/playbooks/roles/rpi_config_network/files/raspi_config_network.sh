#!/bin/bash

# Title         Configure RPi network settings
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux & macOS
# Description   Run RPi settings that affects network configurations
#==============================================================================
run_rpi_network_instructions() {
  # Important:
  # Don't change the following lines unless you know what you are doing
  # They execute the config options starting with 'do_' below
  grep -E -v -e '^\s*#' -e '^\s*$' <<END | \
  sed -e 's/$//' -e 's/^\s*/\/usr\/bin\/raspi-config nonint /' | bash -x -
#
############# INSTRUCTIONS ###########
#
# Change following options starting with 'do_' to suit your configuration
#
# Anything after a has '#' is ignored and used for comments
#
############# EDIT raspi-config SETTINGS BELOW ###########

#
# Network Configuration
#
do_hostname ${HOST_NAME}
${WIFI_COUNTRY}
${WIFI_SSID_PASSPHRASE}

# Don't add any raspi-config configuration options after 'END' line below & don't remove 'END' line
END
}

configure_network_settings() {
  local curr_hostname=$(hostname)

  if [[ "${curr_hostname}" == "${HOST_NAME}" ]]; then
    echo "Hostname is already configured. name: ${curr_hostname}"
  else
    echo "Configuring hostname on remote node. name: ${HOST_NAME}"
    run_rpi_network_instructions
  fi
}

verify_mandatory_variables() {
  if [[ -z "${HOST_NAME}" ]]; then
      echo "Missing mandatory env var. name: HOST_NAME"
      exit 1
  fi
}

main() {
  verify_mandatory_variables
  configure_network_settings
  configure_static_ip_address
}

main "$@"