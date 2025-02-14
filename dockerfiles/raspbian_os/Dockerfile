FROM --platform=linux/arm64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt-get update && apt-get install -y \
    qemu-system-arm \
    qemu-user-static \
    qemu-efi-aarch64 \
    openssh-server \
    wget \
    xz-utils \
    sudo \
    fdisk \
    mount \
    e2fsprogs \
    && apt-get clean

# Create necessary directories
RUN mkdir -p /root/qemu/kernel /root/qemu/mount/boot /root/qemu/mount/root

# Download required kernel and DTB files
RUN wget https://github.com/dhruvvyas90/qemu-rpi-kernel/raw/master/kernel-qemu-4.19.50-buster \
  -O /root/qemu/kernel/kernel-qemu-4.19.50-buster && \
  wget https://github.com/dhruvvyas90/qemu-rpi-kernel/raw/master/versatile-pb.dtb \
  -O /root/qemu/kernel/versatile-pb.dtb

# RUN wget https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2023-12-11/2023-12-11-raspios-bookworm-armhf-lite.img.xz \
#   -O /root/qemu/raspbian.img.xz && \
#   xz -d /root/qemu/raspbian.img.xz

# Copy Raspbian image
COPY raspbian.img /root/qemu/raspbian.img

# Create startup script that will prepare the image at runtime
RUN echo '#!/bin/bash\n\
\n\
echo "Setting up loop device..."\n\
LOOP_DEV=$(losetup -fP --show /root/qemu/raspbian.img)\n\
\n\
echo "Creating mount points..."\n\
mkdir -p /mnt/boot /mnt/root\n\
\n\
echo "Mounting partitions..."\n\
mount ${LOOP_DEV}p1 /mnt/boot\n\
mount ${LOOP_DEV}p2 /mnt/root\n\
\n\
echo "Enabling SSH..."\n\
touch /mnt/boot/ssh\n\
\n\
echo "Configuring system..."\n\
# Enable SSH and password authentication\n\
sed -i "s/#PasswordAuthentication yes/PasswordAuthentication yes/" /mnt/root/etc/ssh/sshd_config\n\
sed -i "s/#PermitRootLogin prohibit-password/PermitRootLogin yes/" /mnt/root/etc/ssh/sshd_config\n\
sed -i "s/#ListenAddress 0.0.0.0/ListenAddress 0.0.0.0/" /mnt/root/etc/ssh/sshd_config\n\
\n\
# Set password for pi user\n\
echo "pi:raspberry" | chroot /mnt/root chpasswd\n\
\n\
echo "Installing prerequisites..."\n\
cp /usr/bin/qemu-arm-static /mnt/root/usr/bin/\n\
\n\
# Prepare chroot environment\n\
cp /etc/resolv.conf /mnt/root/etc/\n\
mount -t proc proc /mnt/root/proc\n\
mount -t sysfs sysfs /mnt/root/sys\n\
mount -o bind /dev /mnt/root/dev\n\
\n\
echo "Installing packages in chroot..."\n\
chroot /mnt/root /usr/bin/qemu-arm-static /bin/bash -c "\n\
    apt-get update && \n\
    apt-get install -y python3 python3-pip openssh-server && \n\
    pip3 install ansible && \n\
    systemctl enable ssh"\n\
\n\
echo "Cleaning up mounts..."\n\
umount /mnt/root/dev\n\
umount /mnt/root/sys\n\
umount /mnt/root/proc\n\
umount /mnt/boot\n\
umount /mnt/root\n\
losetup -d ${LOOP_DEV}\n\
\n\
echo "Starting QEMU..."\n\
exec qemu-system-arm \
    -M versatilepb \
    -cpu arm1176 \
    -m 256 \
    -drive file=/root/qemu/raspbian.img,format=raw \
    -net nic \
    -net user,hostfwd=tcp::2222-:22 \
    -dtb /root/qemu/kernel/versatile-pb.dtb \
    -kernel /root/qemu/kernel/kernel-qemu-4.19.50-buster \
    -append "root=/dev/sda2 panic=1 rootfstype=ext4 rw console=ttyAMA0 dwc_otg.lpm_enable=0" \
    -no-reboot \
    -nographic' > /root/qemu/start.sh && \
    chmod +x /root/qemu/start.sh

EXPOSE 2222

CMD ["/root/qemu/start.sh"]

# # Create script to prepare the image
# RUN echo '#!/bin/bash\n\
# # Enable SSH\n\
# BOOT_OFFSET=1048576\n\
# mount -o loop,offset=$BOOT_OFFSET /root/qemu/raspbian.img /root/qemu/mount/boot\n\
# touch /root/qemu/mount/boot/ssh\n\
# umount /root/qemu/mount/boot\n\
# \n\
# # Modify root filesystem\n\
# ROOT_OFFSET=$(fdisk -l /root/qemu/raspbian.img | grep Linux | awk "{print \\$2 * 512}")\n\
# mount -o loop,offset=$ROOT_OFFSET /root/qemu/raspbian.img /root/qemu/mount/root\n\
# \n\
# # Enable password authentication in SSH\n\
# sed -i "s/#PasswordAuthentication yes/PasswordAuthentication yes/" /root/qemu/mount/root/etc/ssh/sshd_config\n\
# \n\
# # Set up pi user password (default: raspberry)\n\
# echo "pi:raspberry" | chpasswd -R /root/qemu/mount/root\n\
# \n\
# # Install Ansible prerequisites\n\
# cp /usr/bin/qemu-arm-static /root/qemu/mount/root/usr/bin/\n\
# chroot /root/qemu/mount/root /usr/bin/qemu-arm-static /bin/bash -c "\n\
#     apt-get update && \n\
#     apt-get install -y python3 python3-pip && \n\
#     pip3 install ansible"\n\
# \n\
# umount /root/qemu/mount/root' > /root/qemu/prepare-image.sh && \
#     chmod +x /root/qemu/prepare-image.sh

# # Run the preparation script
# RUN /root/qemu/prepare-image.sh

# # Create startup script
# RUN echo '#!/bin/bash\n\
# qemu-system-arm \
#     -M versatilepb \
#     -cpu arm1176 \
#     -m 256 \
#     -drive file=/root/qemu/raspbian.img,format=raw \
#     -net nic \
#     -net user,hostfwd=tcp::2222-:22 \
#     -dtb /root/qemu/kernel/versatile-pb.dtb \
#     -kernel /root/qemu/kernel/kernel-qemu-4.19.50-buster \
#     -append "root=/dev/sda2 panic=1 rootfstype=ext4 rw" \
#     -no-reboot \
#     -nographic' > /root/qemu/start.sh && \
#     chmod +x /root/qemu/start.sh

# EXPOSE 2222

# CMD ["/root/qemu/start.sh"]
