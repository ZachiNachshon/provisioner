# #!/usr/bin/env python3

# import unittest
# from unittest import mock
# from loguru import logger

# from log import LoggerManager

# import logging
# import pytest
# from _pytest.logging import caplog as _caplog
# from loguru import logger

# # These tests need some refinement using caplog for properly checking the verbose flag.
# # Currently these are naive tests and should have tighted assertion in the future chekcing that debug logs don't show on verbose=False


# @pytest.fixture
# def caplog(_caplog):
#     class PropogateHandler(logging.Handler):
#         def emit(self, record):
#             logging.getLogger(record.name).handle(record)

#     handler_id = logger.add(PropogateHandler(), format="{message} {extra}")
#     yield _caplog
#     logger.remove(handler_id)


# def test_some_func_logs_warning(caplog):
#     # log_mgr = LoggerManager()
#     # log_mgr.initialize(verbose=True)
#     logger.debug("test-debug-log")
#     assert "DEBUG" in caplog.text
#     assert "test-debug-log" in caplog.text


# class LoggerTestShould(unittest.TestCase):
#     @mock.patch("loguru.logger.debug")
#     def test_debug_log(self, log_debug_call: mock.MagicMock):
#         log_mgr = LoggerManager()
#         log_mgr.initialize(verbose=True)
#         logger.debug("test-debug-log")
#         self.assertEqual(1, log_debug_call.call_count)

#     @mock.patch("loguru.logger.info")
#     def test_info_log(self, log_info_call: mock.MagicMock):
#         log_mgr = LoggerManager()
#         log_mgr.initialize(verbose=False)
#         logger.info("test-info-log")
#         self.assertEqual(1, log_info_call.call_count)
