#!/usr/bin/env python3


class CliApplicationException(Exception):
    pass


class MissingUtilityException(Exception):
    pass


class MissingPropertiesFileKey(Exception):
    pass


class DownloadFileException(Exception):
    pass


class CliGlobalArgsNotInitialized(Exception):
    pass


class NotInitialized(Exception):
    pass
