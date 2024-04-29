#!/usr/bin/env python3

# 
# This editor module implementation was inspired from:
# https://github.com/fmoo/python-editor/tree/master
# 
from __future__ import print_function
from loguru import logger
import sys
import locale
import os.path
import subprocess
import tempfile

from provisioner.infra.context import Context

__all__ = [
    'edit',
    'get_editor',
    'EditorError',
]

class EditorError(RuntimeError):
    pass

class Editor:

    _dry_run: bool = None
    _verbose: bool = None

    def __init__(self, dry_run: bool, verbose: bool):
        self._dry_run = dry_run
        self._verbose = verbose

    @staticmethod
    def create(ctx: Context) -> "Editor":
        dry_run = ctx.is_dry_run()
        verbose = ctx.is_verbose()
        logger.debug(f"Creating editor (dry_run: {dry_run}, verbose: {verbose})...")
        return Editor(dry_run, verbose)

    def _get_default_editors(self):
        # TODO: Make platform-specific
        return [
            'editor',
            'vim',
            'emacs',
            'nano',
        ]


    def _get_editor_args(self, editor):
        if editor in ['vim', 'gvim', 'vim.basic', 'vim.tiny']:
            return ['-f', '-o']

        elif editor == 'emacs':
            return ['-nw']

        elif editor == 'gedit':
            return ['-w', '--new-window']

        elif editor == 'nano':
            return ['-R']

        elif editor == 'code':
            return ["-w", "-n"]

        else:
            return []


    def _get_editor(self):
        # The import from distutils needs to be here, at this low level to
        # prevent import of 'editor' itself from breaking inquirer. This
        # has to do with ubuntu (debian) python packages artificially
        # separated from distutils.
        #
        # If this import is at top level inquirer breaks on ubuntu until
        # the user explicitly apt-get install python3-distutils. With the
        # import here it will only break if the code is utilizing the
        # inquirer editor prompt.
        try:
            from distutils.spawn import find_executable
        except ImportError:
            from shutil import which as find_executable

        # Get the editor from the environment.  Prefer VISUAL to EDITOR
        editor = os.environ.get('VISUAL') or os.environ.get('EDITOR')
        if editor:
            return editor

        # None found in the environment.  Fallback to platform-specific defaults.
        for ed in self._get_default_editors():
            path = find_executable(ed)
            if path is not None:
                return path

        raise EditorError("Unable to find a viable editor on this system."
            "Please consider setting your $EDITOR variable")


    def _get_tty_filename(self):
        if sys.platform == 'win32':
            return 'CON:'
        return '/dev/tty'


    # def _edit(self, filename=None, contents=None, use_tty=None, suffix=''):
    def _edit(self, filename=None, use_tty=None, suffix=''):
        editor = self._get_editor()
        args = [editor] + self._get_editor_args(os.path.basename(os.path.realpath(editor)))

        if use_tty is None:
            use_tty = sys.stdin.isatty() and not sys.stdout.isatty()

        if filename is None:
            tmp = tempfile.NamedTemporaryFile(suffix=suffix)
            filename = tmp.name

        # if contents is not None:
        #     # For python3 only.  If str is passed instead of bytes, encode default
        #     if hasattr(contents, 'encode'):
        #         contents = contents.encode()

        #     with open(filename, mode='wb') as f:
        #         f.write(contents)

        args += [filename]

        stdout = None
        if use_tty:
            stdout = open(self._get_tty_filename(), 'wb')

        proc = subprocess.Popen(args, close_fds=True, stdout=stdout)
        proc.communicate()

        with open(filename, mode='rb') as f:
            return f.read()

    def _open_file_for_edit(self, filename: str) -> None:
        if self._dry_run:
            return

        self._edit(filename, use_tty=True)
    
    open_file_for_edit_fn = _open_file_for_edit