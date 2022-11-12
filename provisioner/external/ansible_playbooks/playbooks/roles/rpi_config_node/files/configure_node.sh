#!/bin/bash

CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ANSIBLE_TMP_FOLDER_ABS_PATH=$(dirname "${CURRENT_FOLDER_ABS_PATH}")

source "${ANSIBLE_TMP_FOLDER_ABS_PATH}/external/shell_scripts_lib/logger.sh"
source "${ANSIBLE_TMP_FOLDER_ABS_PATH}/external/shell_scripts_lib/cmd.sh"

# This script was inspired from - https://gist.github.com/damoclark/ab3d700aafa140efb97e510650d9b1be
configure_node() {

  echo "Configuring remote RPi node. name: ${HOST_NAME}"

  # Important:
  # Don't change the following lines unless you know what you are doing
  # They execute the config options starting with 'do_' below substituted from ENV vars
  grep -E -v -e '^\s*#' -e '^\s*$' <<END | \
  sed -e 's/$//' -e 's/^\s*/\/usr\/bin\/raspi-config nonint /' | bash -x -
#
############# INSTRUCTIONS ###########
#
# Change following options starting with 'do_' to suit your configuration
#
# Anything after a has '#' is ignored and used for comments
#
# Then drop the file into the boot partition of your SD card
#
# In order to run manually, after booting the Raspberry Pi, login as user 'pi' and run following command:
#
# sudo /boot/raspi-config.txt
#
############# EDIT raspi-config SETTINGS BELOW ###########

#
# raspi-config nonint do_XXX %d
#

#
# Hardware Configuration
#
${BOOT_WAIT}
${BOOT_SPLASH}
${OVERSCAN}
${CAMERA}
${SSH}
${SPI}
${MEMORY_SPLIT}
${I2C}
${SERIAL}
${BOOT_BEHAVIOUR}
${ONEWIRE}
${AUDIO}
${GLDRIVER}
${RGPIO}

#
# System Configuration
#
${CONFIGURE_KEYBOARD}
${CHANGE_TIMEZONE}
${CHANGE_LOCALE}
${WIFI_COUNTRY}
${WIFI_SSID_PASSPHRASE}

# Don't add any raspi-config configuration options after 'END' line below & don't remove 'END' line
END
}

run_custom_commands() {
  echo "Running custom commands..."
  ############# CUSTOM COMMANDS ###########
  # You may add your own custom GNU/Linux commands below this line
  # These commands will execute as the root user

  # Some examples - uncomment by removing '#' in front to test/experiment

  #/usr/bin/raspi-config do_wifi_ssid_passphrase # Interactively configure the wifi network

  #/usr/bin/aptitude update                      # Update the software package information
  #/usr/bin/aptitude upgrade                     # Upgrade installed software to the latest versions

  #/usr/bin/raspi-config do_change_pass          # Interactively set password for your login

  #/sbin/shutdown -r now                         # Reboot after all changes above complete
}

verify_mandatory_variables() {
  if [[ -z "${HOST_NAME}" ]]; then
    echo "Missing mandatory env var. name: HOST_NAME" >&1
    exit 1 
  fi
}

main() {
  verify_mandatory_variables
  configure_node
  run_custom_commands
}

main "$@"