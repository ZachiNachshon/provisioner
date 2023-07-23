#!/usr/bin/env python3


class OsArchInvalidFlagException(Exception):
    pass


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


class FailedToReadConfigurationFile(Exception):
    pass


class FailedToSerializeConfiguration(Exception):
    pass


class InvalidAnsibleHostPair(Exception):
    pass


class StepEvaluationFailure(Exception):
    pass


class AnsiblePlaybookRunnerException(StepEvaluationFailure):
    pass


class CliEntrypointFailure(Exception):
    pass


class InstallerUtilityNotSupported(Exception):
    pass


class MissingCliArgument(Exception):
    pass


class VersionResolverError(Exception):
    pass


class OsArchNotSupported(Exception):
    pass


class InstallerSourceError(Exception):
    pass
