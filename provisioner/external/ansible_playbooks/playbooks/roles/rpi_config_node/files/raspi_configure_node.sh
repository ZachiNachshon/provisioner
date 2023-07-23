#!/bin/bash

CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ANSIBLE_TEMP_FOLDER_PATH="$HOME/.ansible/tmp"
SHELL_SCRIPTS_LIB_IMPORT_PATH="${ANSIBLE_TEMP_FOLDER_PATH}/shell_lib.sh" 

source "${SHELL_SCRIPTS_LIB_IMPORT_PATH}"

RASPI_CONFIG_BINARY=/usr/bin/raspi-config
RASPI_BOOT_CMDLINE=/boot/cmdline.txt

CGROUP_MEMORY="cgroup_memory=1"
CGROUP_ENABLE="cgroup_enable=memory"

has_host_name() {
  [[ -n "${HOST_NAME}" ]]
}

is_boot_wait() {
  [[ -n "${BOOT_WAIT}" ]]
}

is_boot_splash() {
  [[ -n "${BOOT_SPLASH}" ]]
}

is_overscan() {
  [[ -n "${OVERSCAN}" ]]
}

is_camera() {
  [[ -n "${CAMERA}" ]]
}

is_ssh() {
  [[ -n "${SSH}" ]]
}

is_spi() {
  [[ -n "${SPI}" ]]
}

is_memory_split() {
  [[ -n "${MEMORY_SPLIT}" ]]
}

is_i2c() {
  [[ -n "${I2C}" ]]
}

is_serial_bus() {
  [[ -n "${SERIAL_BUS}" ]]
}

is_boot_behaviour() {
  [[ -n "${BOOT_BEHAVIOUR}" ]]
}

is_onewire() {
  [[ -n "${ONEWIRE}" ]]
}

is_audio() {
  [[ -n "${AUDIO}" ]]
}

is_gldriver() {
  [[ -n "${GLDRIVER}" ]]
}

is_rgpio() {
  [[ -n "${RGPIO}" ]]
}

is_configure_keyboard() {
  [[ -n "${CONFIGURE_KEYBOARD}" ]]
}

is_change_timezone() {
  [[ -n "${CHANGE_TIMEZONE}" ]]
}

is_change_locale() {
  [[ -n "${CHANGE_LOCALE}" ]]
}

configure_node_system() {
  log_info "Configuring remote RPi node system. name: ${HOST_NAME}"

  if is_configure_keyboard; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${CONFIGURE_KEYBOARD}"
    log_indicator_good "Specify US Keyboard"
  fi

  if is_change_timezone; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${CHANGE_TIMEZONE}"
    log_indicator_good "Change timezone to Asia Jerusalem"
  fi

  if is_change_locale; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${CHANGE_LOCALE}"
    log_indicator_good "Set language to en_US English"
  fi
}

configure_node_hardware() {
  log_info "Configuring remote RPi node hardware. name: ${HOST_NAME}"

  if is_boot_wait; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${BOOT_WAIT}"
    log_indicator_good "Do not wait for network before booting"
  fi

  if is_boot_splash; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${BOOT_SPLASH}"
    log_indicator_good "Disable the splash screen"
  fi

  if is_overscan; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${OVERSCAN}"
    log_indicator_good "Disable overscan"
  fi

  if is_camera; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${CAMERA}"
    log_indicator_good "Disable the camera"
  fi

  if is_ssh; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${SSH}"
    log_indicator_good "Enable remote ssh login"
  fi

  if is_spi; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${SPI}"
    log_indicator_good "Disable spi bus"
  fi

  if is_memory_split; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${MEMORY_SPLIT}"
    log_indicator_good "Set the GPU memory limit to minimum (16MB)"
  fi

  if is_i2c; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${I2C}"
    log_indicator_good "Disable the i2c bus"
  fi

  if is_serial_bus; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${SERIAL_BUS}"
    log_indicator_good "Disable the RS232 serial bus"
  fi

  if is_boot_behaviour; then
    if [[ "${BOOT_BEHAVIOUR}" == "do_boot_behaviour B1" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${BOOT_BEHAVIOUR}"
      log_indicator_good "Boot to CLI & require login"
    elif [[ "${BOOT_BEHAVIOUR}" == "do_boot_behaviour B2" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${BOOT_BEHAVIOUR}"
      log_indicator_good "Boot to CLI & auto login as pi user"
    elif [[ "${BOOT_BEHAVIOUR}" == "do_boot_behaviour B3" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${BOOT_BEHAVIOUR}"
      log_indicator_good "Boot to Graphical & require login"
    elif [[ "${BOOT_BEHAVIOUR}" == "do_boot_behaviour B4" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${BOOT_BEHAVIOUR}"
      log_indicator_good "Boot to Graphical & auto login as pi user"
    else
      log_warning "Invalid boot behavior value ${BOOT_BEHAVIOUR}. options: B1/B1/B3/B4"
    fi
  fi

  if is_onewire; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${ONEWIRE}"
    log_indicator_good "Disable onewire on GPIO4"
  fi

  if is_audio; then
    if [[ "${AUDIO}" == "do_audio 0" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${AUDIO}"
      log_indicator_good "Auto select audio output device"
    elif [[ "${AUDIO}" == "do_audio 1" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${AUDIO}"
      log_indicator_good "Force audio output through 3.5mm analogue jack"
    elif [[ "${AUDIO}" == "do_audio 2" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${AUDIO}"
      log_indicator_good "Force audio output through HDMI digital interface"
    else
      log_warning "Invalid audio value ${AUDIO}. options: 0/1/2"
    fi
  fi

  if is_gldriver; then
    if [[ "${GLDRIVER}" == "do_gldriver G1" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${GLDRIVER}"
      log_indicator_good "Enable Full KMS Opengl Driver - must install deb package first"
    elif [[ "${GLDRIVER}" == "do_gldriver G2" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${GLDRIVER}"
      log_indicator_good "Enable Fake KMS Opengl Driver - must install deb package first"
    elif [[ "${GLDRIVER}" == "do_gldriver G3" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${GLDRIVER}"
      log_indicator_good "Disable opengl driver (default)"
    else
      log_warning "Invalid audio value ${GLDRIVER}. options: G1/G2/G3"
    fi
  fi

  if is_rgpio; then
    log_indicator_good "Disable gpio server - must install deb package first"
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${RGPIO}"
  fi
}

verify_mandatory_variables() {
  if ! has_host_name; then
    log_fatal "Missing mandatory env var. name: HOST_NAME"
  fi

  if ! is_dry_run && ! is_file_exist "${RASPI_CONFIG_BINARY}"; then
    log_fatal "Missing mandatory RPi utility. path: ${RASPI_CONFIG_BINARY}"
  fi
}

verify_supported_os() {
  local os_type=$(read_os_type)
  if ! is_dry_run && [[ "${os_type}" != "linux" ]]; then
    log_fatal "OS is not supported. type: ${os_type}"
  fi
}

# Need to update cgroups on RPI (https://docs.k3s.io/advanced#raspberry-pi)
maybe_update_cgroups() {
  log_info "Updating cgroup module in iptables"
  if ! is_file_contain "${RASPI_BOOT_CMDLINE}" "${CGROUP_MEMORY}"; then
    cmd_run "echo ${CGROUP_MEMORY} >> ${RASPI_BOOT_CMDLINE}"
    log_indicator_good "Added ${CGROUP_MEMORY} to ${RASPI_BOOT_CMDLINE}"
  fi
  if ! is_file_contain "${RASPI_BOOT_CMDLINE}" "${CGROUP_ENABLE}"; then
    cmd_run "echo ${CGROUP_ENABLE} >> ${RASPI_BOOT_CMDLINE}"
    log_indicator_good "Added ${CGROUP_ENABLE} to ${RASPI_BOOT_CMDLINE}"
  fi
}

main() {
  evaluate_run_mode
  verify_supported_os
  verify_mandatory_variables

  if is_verbose; then
  echo """
Instructions: 
  Selected      - 0
  Not-selected  - 1
"""
  fi

  configure_node_hardware
  new_line
  configure_node_system
  new_line
  maybe_update_cgroups
}

main "$@"














# run_custom_commands() {
#   echo "Running custom commands..."
#   ############# CUSTOM COMMANDS ###########
#   # You may add your own custom GNU/Linux commands below this line
#   # These commands will execute as the root user

#   # Some examples - uncomment by removing '#' in front to test/experiment

#   #/usr/bin/raspi-config do_wifi_ssid_passphrase # Interactively configure the wifi network

#   #/usr/bin/aptitude update                      # Update the software package information
#   #/usr/bin/aptitude upgrade                     # Upgrade installed software to the latest versions

#   #/usr/bin/raspi-config do_change_pass          # Interactively set password for your login

#   #/sbin/shutdown -r now                         # Reboot after all changes above complete
# }