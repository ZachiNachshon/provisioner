#!/bin/bash
# Force unbuffered output to prevent hanging appearance
exec 1>/dev/stdout
exec 2>/dev/stderr

CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ANSIBLE_TEMP_FOLDER_PATH="/tmp"
SHELL_SCRIPTS_LIB_IMPORT_PATH="${ANSIBLE_TEMP_FOLDER_PATH}/shell_lib.sh" 

source "${SHELL_SCRIPTS_LIB_IMPORT_PATH}"

# Add debugging output to help diagnose issues
echo "Script started, sourced shell lib from: ${SHELL_SCRIPTS_LIB_IMPORT_PATH}"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"

RASPI_CONFIG_BINARY=/usr/bin/raspi-config
RASPI_BOOT_CMDLINE=/boot/firmware/cmdline.txt
RASPI_CONFIG_TXT="/boot/firmware/config.txt"

CGROUP_MEMORY="cgroup_memory=1"
CGROUP_ENABLE="cgroup_enable=memory"

has_host_name() {
  [[ -n "${HOST_NAME}" ]]
}

is_boot_splash() {
  [[ -n "${BOOT_SPLASH}" ]]
}

is_overscan() {
  [[ -n "${OVERSCAN}" ]]
}

is_spi() {
  [[ -n "${SPI}" ]]
}

is_i2c() {
  [[ -n "${I2C}" ]]
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

is_rgpio() {
  [[ -n "${RGPIO}" ]]
}

is_configure_keyboard() {
  [[ -n "${CONFIGURE_KEYBOARD}" ]]
}

is_change_timezone() {
  [[ -n "${CHANGE_TIMEZONE}" ]]
}

get_locale() {
  [[ -n "${LOCALE}" ]]
}

configure_node_system() {
  echo "==== Configuring remote RPi system settings. name: ${HOST_NAME} ===="
  new_line

  if is_configure_keyboard; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${CONFIGURE_KEYBOARD}"
    log_indicator_good "US Keyboard successfully configured"
  fi

  if is_change_timezone; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${CHANGE_TIMEZONE}"
    log_indicator_good "Timezone successfully changed to UTC"
  fi

  if get_locale; then
    local locale_file="/etc/locale.gen"
    cmd_run "sudo sed -i '/^# *${LOCALE} UTF-8/s/^# *//' ${locale_file}"
    cmd_run "sudo locale-gen"
    cmd_run "sudo update-locale LANG=${LOCALE}"
    log_indicator_good "Locale successfully set to ${LOCALE}"
  fi
}

configure_node_hardware() {
  echo "=== Configuring remote RPi node hardware. name: ${HOST_NAME} ==="
  new_line

  if is_boot_splash; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${BOOT_SPLASH}"
    log_indicator_good "Splash screen successfully disabled"
  fi

  if is_overscan; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${OVERSCAN}"
    log_indicator_good "Overscan successfully disabled"
  fi

  if is_spi; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${SPI}"
    log_indicator_good "SPI bus successfully disabled"
  fi

  if is_i2c; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${I2C}"
    log_indicator_good "I2C bus successfully disabled"
  fi

  if is_boot_behaviour; then
    if [[ "${BOOT_BEHAVIOUR}" == "do_boot_behaviour B1" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${BOOT_BEHAVIOUR}"
      log_indicator_good "Boot to CLI & require login"
    else
      log_indicator_bad "Invalid boot behavior value ${BOOT_BEHAVIOUR}, only B1 is supported"
    fi
  fi

  if is_onewire; then
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${ONEWIRE}"
    log_indicator_good "Onewire on GPIO4 successfully disabled"
  fi

  if is_audio; then
    if [[ "${AUDIO}" == "do_audio 0" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${AUDIO}"
      log_indicator_good "Audio output device successfully auto selected"
    elif [[ "${AUDIO}" == "do_audio 1" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${AUDIO}"
      log_indicator_good "Audio output through 3.5mm analogue jack successfully enabled"
    elif [[ "${AUDIO}" == "do_audio 2" ]]; then
      cmd_run "${RASPI_CONFIG_BINARY} nonint ${AUDIO}"
      log_indicator_good "Audio output through HDMI digital interface successfully enabled"
    else
      log_warning "Invalid audio value ${AUDIO}. options: 0/1/2"
    fi
  fi

  if is_rgpio; then
    log_indicator_good "GPIO server successfully disabled"
    cmd_run "${RASPI_CONFIG_BINARY} nonint ${RGPIO}"
  fi
}

verify_mandatory_variables() {
  if ! has_host_name; then
    log_fatal "Missing mandatory env var. name: HOST_NAME"
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
  echo "=== Updating cgroup parameters in boot command line ==="
  new_line
  local modified=false
  
  if ! is_dry_run; then
    # Read current cmdline content
    local cmdline_content=$(cat ${RASPI_BOOT_CMDLINE})
    
    # Check and add cgroup_memory parameter if not present
    if ! echo "$cmdline_content" | grep -q "${CGROUP_MEMORY}"; then
      cmdline_content="${cmdline_content} ${CGROUP_MEMORY}"
      modified=true
      log_indicator_good "Will add ${CGROUP_MEMORY} to boot command line"
    fi
    
    # Check and add cgroup_enable parameter if not present
    if ! echo "$cmdline_content" | grep -q "${CGROUP_ENABLE}"; then
      cmdline_content="${cmdline_content} ${CGROUP_ENABLE}"
      modified=true
      log_indicator_good "Will add ${CGROUP_ENABLE} to boot command line"
    fi
    
    # Write updated content back to file if modified
    if [ "$modified" = true ]; then
      echo "$cmdline_content" > ${RASPI_BOOT_CMDLINE}
      log_warning "Boot command line updated. A system reboot is required before these changes take effect."
      log_warning "Please reboot the system using: sudo reboot"
    else
      log_info "Cgroup parameters already present in boot command line"
    fi
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
  
  new_line
  echo "Script completed successfully"
}

main "$@"
