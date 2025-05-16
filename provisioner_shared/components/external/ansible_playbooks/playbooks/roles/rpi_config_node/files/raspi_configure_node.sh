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

is_camera() {
  [[ -n "${CAMERA}" ]]
}

is_spi() {
  [[ -n "${SPI}" ]]
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

run_raspi_config() {
  local command=$1
  local message=$2
  
  echo "Executing configuration command: ${command}"
  
  # Extract the operation from the command
  local operation=$(echo "$command" | awk '{print $1}')
  
  case "$operation" in
    "do_boot_splash")
      if [[ "$command" == *"1"* ]]; then
        echo "Disabling splash screen in config.txt"
        grep -q "^disable_splash=" ${RASPI_CONFIG_TXT} && sed -i 's/^disable_splash=.*/disable_splash=1/' ${RASPI_CONFIG_TXT} || echo "disable_splash=1" >> ${RASPI_CONFIG_TXT}
      else
        echo "Enabling splash screen in config.txt"
        grep -q "^disable_splash=" ${RASPI_CONFIG_TXT} && sed -i 's/^disable_splash=.*/disable_splash=0/' ${RASPI_CONFIG_TXT} || echo "disable_splash=0" >> ${RASPI_CONFIG_TXT}
      fi
      ;;
    "do_overscan")
      if [[ "$command" == *"1"* ]]; then
        echo "Disabling overscan in config.txt"
        grep -q "^disable_overscan=" ${RASPI_CONFIG_TXT} && sed -i 's/^disable_overscan=.*/disable_overscan=1/' ${RASPI_CONFIG_TXT} || echo "disable_overscan=1" >> ${RASPI_CONFIG_TXT}
      else
        echo "Enabling overscan in config.txt"
        grep -q "^disable_overscan=" ${RASPI_CONFIG_TXT} && sed -i 's/^disable_overscan=.*/disable_overscan=0/' ${RASPI_CONFIG_TXT} || echo "disable_overscan=0" >> ${RASPI_CONFIG_TXT}
      fi
      ;;
    "do_camera")
      if [[ "$command" == *"1"* ]]; then
        echo "Disabling camera in config.txt"
        grep -q "^camera_auto_detect=" ${RASPI_CONFIG_TXT} && sed -i 's/^camera_auto_detect=.*/camera_auto_detect=0/' ${RASPI_CONFIG_TXT} || echo "camera_auto_detect=0" >> ${RASPI_CONFIG_TXT}
      else
        echo "Enabling camera in config.txt"
        grep -q "^camera_auto_detect=" ${RASPI_CONFIG_TXT} && sed -i 's/^camera_auto_detect=.*/camera_auto_detect=1/' ${RASPI_CONFIG_TXT} || echo "camera_auto_detect=1" >> ${RASPI_CONFIG_TXT}
      fi
      ;;
    "do_spi")
      if [[ "$command" == *"1"* ]]; then
        echo "Disabling SPI in config.txt"
        grep -q "^dtparam=spi=" ${RASPI_CONFIG_TXT} && sed -i 's/^dtparam=spi=.*/dtparam=spi=off/' ${RASPI_CONFIG_TXT} || echo "dtparam=spi=off" >> ${RASPI_CONFIG_TXT}
      else
        echo "Enabling SPI in config.txt"
        grep -q "^dtparam=spi=" ${RASPI_CONFIG_TXT} && sed -i 's/^dtparam=spi=.*/dtparam=spi=on/' ${RASPI_CONFIG_TXT} || echo "dtparam=spi=on" >> ${RASPI_CONFIG_TXT}
      fi
      ;;
    "do_i2c")
      if [[ "$command" == *"1"* ]]; then
        echo "Disabling I2C in config.txt"
        grep -q "^dtparam=i2c_arm=" ${RASPI_CONFIG_TXT} && sed -i 's/^dtparam=i2c_arm=.*/dtparam=i2c_arm=off/' ${RASPI_CONFIG_TXT} || echo "dtparam=i2c_arm=off" >> ${RASPI_CONFIG_TXT}
      else
        echo "Enabling I2C in config.txt"
        grep -q "^dtparam=i2c_arm=" ${RASPI_CONFIG_TXT} && sed -i 's/^dtparam=i2c_arm=.*/dtparam=i2c_arm=on/' ${RASPI_CONFIG_TXT} || echo "dtparam=i2c_arm=on" >> ${RASPI_CONFIG_TXT}
      fi
      ;;
    "do_onewire")
      if [[ "$command" == *"1"* ]]; then
        echo "Disabling OneWire in config.txt"
        sed -i '/^dtoverlay=w1-gpio/d' ${RASPI_CONFIG_TXT}
      else
        echo "Enabling OneWire in config.txt"
        grep -q "^dtoverlay=w1-gpio" ${RASPI_CONFIG_TXT} || echo "dtoverlay=w1-gpio,gpiopin=4" >> ${RASPI_CONFIG_TXT}
      fi
      ;;
    "do_audio")
      if [[ "$command" == *"0"* ]]; then
        echo "Setting audio to auto in config.txt"
        grep -q "^dtparam=audio=" ${RASPI_CONFIG_TXT} && sed -i 's/^dtparam=audio=.*/dtparam=audio=on/' ${RASPI_CONFIG_TXT} || echo "dtparam=audio=on" >> ${RASPI_CONFIG_TXT}
      elif [[ "$command" == *"1"* ]]; then
        echo "Setting audio to 3.5mm jack in config.txt"
        grep -q "^dtparam=audio=" ${RASPI_CONFIG_TXT} && sed -i 's/^dtparam=audio=.*/dtparam=audio=1/' ${RASPI_CONFIG_TXT} || echo "dtparam=audio=1" >> ${RASPI_CONFIG_TXT}
      elif [[ "$command" == *"2"* ]]; then
        echo "Setting audio to HDMI in config.txt"
        grep -q "^dtparam=audio=" ${RASPI_CONFIG_TXT} && sed -i 's/^dtparam=audio=.*/dtparam=audio=2/' ${RASPI_CONFIG_TXT} || echo "dtparam=audio=2" >> ${RASPI_CONFIG_TXT}
      fi
      ;;
    "do_boot_behaviour")
      # Force boot to CLI with login - B1 only
      echo "Setting boot to CLI with login"
      systemctl set-default multi-user.target
      # Disable autologin if enabled
      if [ -f /etc/systemd/system/getty@tty1.service.d/autologin.conf ]; then
        rm /etc/systemd/system/getty@tty1.service.d/autologin.conf
      fi
      ;;
    "do_configure_keyboard")
      echo "Setting keyboard layout to US"
      cat > /etc/default/keyboard << EOF
XKBMODEL="pc105"
XKBLAYOUT="us"
XKBVARIANT=""
XKBOPTIONS=""
BACKSPACE="guess"
EOF
      # Apply the settings
      dpkg-reconfigure -f noninteractive keyboard-configuration
      ;;
    "do_change_timezone")
      echo "Setting timezone to UTC"
      ln -sf /usr/share/zoneinfo/UTC /etc/localtime
      ;;
    "do_change_locale")
      echo "Setting locale to en_US.UTF-8"
      sed -i 's/^# *en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen
      locale-gen
      update-locale LANG=en_US.UTF-8
      ;;
    "do_gldriver")
      if [[ "$command" == *"G1"* ]]; then
        echo "Enabling Full KMS OpenGL Driver"
        grep -q "^dtoverlay=vc4-kms-v3d" ${RASPI_CONFIG_TXT} || echo "dtoverlay=vc4-kms-v3d" >> ${RASPI_CONFIG_TXT}
      elif [[ "$command" == *"G2"* ]]; then
        echo "Enabling Fake KMS OpenGL Driver"
        grep -q "^dtoverlay=vc4-fkms-v3d" ${RASPI_CONFIG_TXT} || echo "dtoverlay=vc4-fkms-v3d" >> ${RASPI_CONFIG_TXT}
      elif [[ "$command" == *"G3"* ]]; then
        echo "Disabling OpenGL Driver"
        sed -i '/^dtoverlay=vc4-kms-v3d/d' ${RASPI_CONFIG_TXT}
        sed -i '/^dtoverlay=vc4-fkms-v3d/d' ${RASPI_CONFIG_TXT}
      fi
      ;;
    "do_rgpio")
      if [[ "$command" == *"0"* ]]; then
        echo "Enabling GPIO server"
        systemctl enable pigpiod
      else
        echo "Disabling GPIO server"
        systemctl disable pigpiod
      fi
      ;;
    *)
      echo "WARNING: Unsupported operation: $operation. Cannot process this configuration."
      ;;
  esac
  
  log_indicator_good "${message}"
  new_line
  return 0
}

configure_node_system() {
  echo "==== Configuring remote RPi node system. name: ${HOST_NAME} ===="
  new_line

  if is_configure_keyboard; then
    run_raspi_config "${CONFIGURE_KEYBOARD}" "US Keyboard successfully configured"
  fi

  if is_change_timezone; then
    run_raspi_config "${CHANGE_TIMEZONE}" "Timezone successfully changed to Asia Jerusalem"
  fi

  if is_change_locale; then
    run_raspi_config "${CHANGE_LOCALE}" "Locale successfully set to en_US.UTF-8"
  fi
}

configure_node_hardware() {
  log_info "Configuring remote RPi node hardware. name: ${HOST_NAME}"

  if is_boot_splash; then
    run_raspi_config "${BOOT_SPLASH}" "Splash screen successfully disabled"
  fi

  if is_overscan; then
    run_raspi_config "${OVERSCAN}" "Overscan successfully disabled"
  fi

  if is_camera; then
    run_raspi_config "${CAMERA}" "Camera successfully disabled"
  fi

  if is_spi; then
    run_raspi_config "${SPI}" "SPI bus successfully disabled"
  fi

  if is_i2c; then
    run_raspi_config "${I2C}" "I2C bus successfully disabled"
  fi

  if is_serial_bus; then
    run_raspi_config "${SERIAL_BUS}" "RS232 serial bus successfully disabled"
  fi

  if is_boot_behaviour; then
    run_raspi_config "${BOOT_BEHAVIOUR}" "Boot to CLI & require login"
  fi

  if is_onewire; then
    run_raspi_config "${ONEWIRE}" "Onewire on GPIO4 disabled"
  fi

  if is_audio; then
    if [[ "${AUDIO}" == "do_audio 0" ]]; then
      run_raspi_config "${AUDIO}" "Audio output device auto selected"
    elif [[ "${AUDIO}" == "do_audio 1" ]]; then
      run_raspi_config "${AUDIO}" "Audio output through 3.5mm analogue jack"
    elif [[ "${AUDIO}" == "do_audio 2" ]]; then
      run_raspi_config "${AUDIO}" "Audio output through HDMI digital interface"
    else
      log_warning "Invalid audio value ${AUDIO}. options: 0/1/2"
    fi
  fi

  if is_gldriver; then
    if [[ "${GLDRIVER}" == "do_gldriver G1" ]]; then
      run_raspi_config "${GLDRIVER}" "Enable Full KMS Opengl Driver - must install deb package first"
    elif [[ "${GLDRIVER}" == "do_gldriver G2" ]]; then
      run_raspi_config "${GLDRIVER}" "Enable Fake KMS Opengl Driver - must install deb package first"
    elif [[ "${GLDRIVER}" == "do_gldriver G3" ]]; then
      run_raspi_config "${GLDRIVER}" "OpenGL driver disabled"
    else
      log_warning "Invalid audio value ${GLDRIVER}. options: G1/G2/G3"
    fi
  fi

  if is_rgpio; then
    run_raspi_config "${RGPIO}" "GPIO server disabled"
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
  log_info "Updating cgroup parameters in boot command line"
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
  echo "Starting main function"
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
  
  echo "Script completed successfully"
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