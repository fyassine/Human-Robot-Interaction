"""This class is used to log debug and info messages.

Author:
    Daniil Zauzolkov
Contributor:
    Simon Dobers
    Jakob Thumm
"""

import logging
import sys


class LoggingHelper:
    """Helper class to adjust logging."""

    @staticmethod
    def init_logger(logger, extended_logging):
        """Adjust the given logger object.

        Sets the proper formatting and handler.

        :param logger: The logger object to adjust.
        :param extended_logging: If True the logger level will be set to DEBUG
            otherwise to INFO.
        :return: None
        """
        level = logging.DEBUG if extended_logging else logging.INFO
        logger.setLevel(level)

        # This is required, otherwise, when multiple instances
        # are running, the message will be output multiple times
        if logger.hasHandlers():
            return

        handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(handler)

    @staticmethod
    def init_logging(extended_logging):
        """Initialize the top level logging.

        :param extended_logging: If True the logger level will be set to DEBUG
            otherwise to INFO.
        :return: None
        """
        level = logging.DEBUG if extended_logging else logging.INFO

        logging.basicConfig(
            format="[%(asctime)s] %(name)s - %(levelname)s: %(message)s",
            level=level
        )
