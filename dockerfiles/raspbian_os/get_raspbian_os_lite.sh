#!/bin/bash

  wget https://downloads.raspberrypi.org/raspios_lite_armhf_latest
  xz -d 2024-11-19-raspios-bookworm-armhf-lite.img.xz
  # xz -d *.img.xz
  mv *.img raspbian.img