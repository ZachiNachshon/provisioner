# Use the official slim Python image
FROM python:3.11-slim

# Install necessary packages including OpenSSH and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server sudo curl wget systemd \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
    # ansible \

# Install locales package and generate en_US.UTF-8
RUN apt-get update && apt-get install -y locales \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen en_US.UTF-8 \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

# Set environment variables for locale
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

# Use a recognized terminal in the container to support TUI Python libraries terminal environment
RUN echo 'export TERM=xterm' >> /etc/bash.bashrc

# Create the 'pi' user and set password
RUN useradd -m -s /bin/bash pi && echo 'pi:raspberry' | chpasswd

# Allow 'pi' user to use sudo without password
RUN usermod -aG sudo pi && echo 'pi ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/pi

# Create a dedicated 'admin' user for administrative tasks
RUN useradd -m -s /bin/bash admin && echo 'admin:admin' | chpasswd

# Allow 'admin' user to use sudo without password
RUN usermod -aG sudo admin && echo 'admin ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/admin

# Set up SSH
RUN mkdir /var/run/sshd && \
    ssh-keygen -A && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config

# Expose SSH port
EXPOSE 22

# Update python3 to point to python3.11 explicitly (optional, since it's the default)
RUN update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.11 1

# Start the SSH service
CMD ["/usr/sbin/sshd", "-D"]