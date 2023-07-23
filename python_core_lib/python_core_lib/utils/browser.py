#!/usr/bin/env python3

import webbrowser

from loguru import logger


def open_browser(url: str):
    logger.info("Opening browser. url: {}", url)
    webbrowser.open(url=url, new=2)
