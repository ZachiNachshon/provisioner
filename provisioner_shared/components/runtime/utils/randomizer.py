#!/usr/bin/env python3

import binascii
import crypt
import os
import platform
from enum import Enum

from loguru import logger

from provisioner_shared.components.runtime.infra.context import Context


class HashMethod(Enum):
    SHA256 = "5"  # crypt SHA-256
    SHA512 = "6"  # crypt SHA-512


class Randomizer:

    _dry_run: bool = None
    _verbose: bool = None

    def __init__(self, dry_run: bool, verbose: bool):
        self._dry_run = dry_run
        self._verbose = verbose

    @staticmethod
    def create(ctx: Context) -> "Randomizer":
        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        logger.debug(f"Creating randomizer utility (dry_run: {dry_run}, verbose: {verbose})...")
        return Randomizer(dry_run, verbose)

    def _hash_password(self, password: str, method: HashMethod = HashMethod.SHA256) -> str:
        """
        Hash a password using the specified hash method, compatible with openssl passwd.

        Args:
            password: The password to hash
            method: The hash method to use (default: SHA256)

        Returns:
            str: The hashed password, in the format: $id$salt$hash
        """
        if self._dry_run:
            method_name = method.name
            return f"DRY_RUN_{method_name}_HASH_{password}"

        # Generate a random salt (8 alphanumeric chars)
        salt = binascii.hexlify(os.urandom(4)).decode("ascii")[:8]

        # Equivalent to openssl passwd -6 (or -5 for SHA256)
        # This creates a hash compatible with /etc/shadow format
        method_id = method.value

        # On Linux, use the standard crypt module
        if platform.system() == "Linux":
            salt_str = f"${method_id}${salt}$"
            hashed = crypt.crypt(password, salt_str)
            return hashed

        # On macOS or other platforms, ensure proper SHA support with passlib
        if method == HashMethod.SHA512:
            # SHA512 crypt is $6$salt$hash
            from passlib.hash import sha512_crypt

            hashed = sha512_crypt.using(salt=salt, rounds=5000).hash(password)
            return hashed
        else:
            # SHA256 crypt is $5$salt$hash
            from passlib.hash import sha256_crypt

            hashed = sha256_crypt.using(salt=salt, rounds=5000).hash(password)
            return hashed

    hash_password_fn = _hash_password
