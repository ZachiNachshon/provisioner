FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8

# Install required packages and locales
RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    python3 \
    python3-pip \
    locales \
    systemd \
    systemd-sysv \
    dhcpcd5 \
    && apt-get clean

# Generate locales
RUN locale-gen en_US.UTF-8

# Create pi user (similar to Raspberry Pi)
RUN useradd -m -s /bin/bash pi && \
    echo "pi:raspberry" | chpasswd && \
    adduser pi sudo && \
    echo 'pi ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/pi

# Configure SSH
RUN mkdir /var/run/sshd && \
    sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Create mock raspi-config
RUN echo '#!/bin/bash\n\
if [ "$1" = "nonint" ]; then\n\
    shift\n\
    echo "Mock raspi-config: $@"\n\
    exit 0\n\
fi\n\
exit 1' > /usr/bin/raspi-config && \
    chmod +x /usr/bin/raspi-config

# Create mock boot/cmdline.txt
RUN mkdir -p /boot && \
    echo "console=serial0,115200 console=tty1 root=PARTUUID=738a4d67-02 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait" > /boot/cmdline.txt

# Setup dhcpcd configuration
RUN mkdir -p /etc/dhcpcd && \
    touch /etc/dhcpcd.conf && \
    chmod 666 /etc/dhcpcd.conf && \
    chown root:root /etc/dhcpcd.conf && \
    chmod 755 /etc/dhcpcd && \
    chown root:root /etc/dhcpcd

# Create mock systemd service for dhcpcd
RUN echo '[Unit]\n\
Description=DHCP Client Daemon\n\
After=network.target\n\
\n\
[Service]\n\
Type=simple\n\
ExecStart=/usr/sbin/dhcpcd\n\
Restart=always\n\
\n\
[Install]\n\
WantedBy=multi-user.target' > /etc/systemd/system/dhcpcd.service && \
    chmod 644 /etc/systemd/system/dhcpcd.service && \
    chown root:root /etc/systemd/system/dhcpcd.service

# Create mock systemctl
RUN echo '#!/bin/bash\n\
if [ "$1" = "start" ] || [ "$1" = "enable" ]; then\n\
    echo "Mock systemctl: $1 $2"\n\
    exit 0\n\
fi\n\
exit 1' > /usr/bin/systemctl && \
    chmod +x /usr/bin/systemctl

# Install Ansible
RUN pip3 install ansible

# Ensure Ansible temp directory exists and has correct permissions
RUN mkdir -p /home/pi/.ansible/tmp && \
    chown -R pi:pi /home/pi/.ansible && \
    chmod -R 755 /home/pi/.ansible

EXPOSE 22

# Start the SSH service
CMD ["/usr/sbin/sshd", "-D"] 