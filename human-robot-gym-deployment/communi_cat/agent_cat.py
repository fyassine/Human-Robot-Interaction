"""This class is used to send data to the real Schunk robot.

Author:
    Daniil Zauzolkov
Contributor:
    Simon Dobers
    Jakob Thumm
"""

import logging

from socket import socket, AF_INET, SOCK_DGRAM
from struct import pack

from communi_cat.config_cat import ConfigCat
from communi_cat.logging_helper import LoggingHelper


class AgentCat:
    """Class sending data via UDP to the real robot.

    This class allows to send data to the provided IP over UDP.
    IP and port can be provided as argument, otherwise will be
    read from the configuration file.

    :arg ip_address: The IP address to send the data to.
    :arg port: The port to send the data to.
    """

    def __init__(self, ip_address=None, port=None, extended_logging=False):
        """Initialize an object instance.

        :param ip_address: The IP address of the receiver, otherwise the IP
            from the configuration will be used.
        :param port: The port of the receiver, otherwise the port from the
            configuration will be used.
        :param extended_logging: Allows to activate or disable extended
            logging. By default set to False.
        """
        if ip_address is None or port is None:
            self._config = ConfigCat().config

        self.ip_address = ip_address if ip_address else self._config['networking']['target_ip_address']
        self.port = port if port else self._config['networking']['target_port']
        self._extended_logging = extended_logging
        self._sock = None

        LoggingHelper.init_logging(extended_logging)

        self._logger = logging.getLogger('AgentCat')
        LoggingHelper.init_logger(self._logger, extended_logging)

    def start(self):
        """Start the socket and binds to it.

        :return: None
        """
        self._logger.info('Initialize sender socket to %s:%s', self.ip_address, self.port)

        self._sock = socket(AF_INET, SOCK_DGRAM)
        self._sock.connect((self.ip_address, self.port))

        self._logger.info('Socket initialized. Connected to %s:%s', self.ip_address, self.port)

    def stop(self):
        """Stop the socket.

        :return: None
        """
        self._sock.close()
        self._logger.info('Socket closed.')

    def send_data(self, data):
        """Send the provided data to the target.

        :param data: The data to send, which should be an array of doubles.
        :return: None
        """
        data_size = len(data)
        buffer = pack(f'<{data_size}d', *data)

        self._logger.debug('Sending %s doubles: %s', data_size, data)

        self._sock.send(buffer)
