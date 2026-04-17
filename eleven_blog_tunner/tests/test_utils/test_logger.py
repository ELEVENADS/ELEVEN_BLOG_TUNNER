import pytest
from eleven_blog_tunner.utils.logger import logger_instance

class TestLogger:
    def test_logger_instance_exists(self):
        assert logger_instance is not None

    def test_logger_can_log_info(self):
        logger_instance.info("Test info message")

    def test_logger_can_log_error(self):
        logger_instance.error("Test error message")

    def test_logger_can_log_warning(self):
        logger_instance.warning("Test warning message")

    def test_logger_can_log_debug(self):
        logger_instance.debug("Test debug message")
