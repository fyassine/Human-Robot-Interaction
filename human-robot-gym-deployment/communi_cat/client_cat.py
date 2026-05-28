"""This script is used to receive data from the robot via UDP.

Author:
    Daniil Zauzolkov
    Simon Dobers
    Jakob Thumm
Date:
    31.01.2022
"""
import logging
import numpy as np
import time

from os import path, makedirs
from socket import socket, AF_INET, SOCK_DGRAM, timeout
from struct import unpack

from communi_cat.config_cat import ConfigCat
from communi_cat.logging_helper import LoggingHelper


class ClientCat:
    """Responsible for receiving and saving data from UDP.

    This class converts the received data to a numpy format.
    It allows to save the data to a .npy file.

    :arg ip_address: The local IP address where to receive the data from.
    :arg port: The local port where to receive the data from.
    :arg data: The data that was received (initially empty).
    """

    _TIMEOUT = 3
    _BUFFER_SIZE = 2048

    def __init__(
        self,
        client_name: str = 'ReceiverCat',
        ip_address: str = None,
        port: int = None,
        extended_logging: bool = False
    ):
        """Initialize the ClientCat class.

        :param ip_address: The local IP address where to receive the data from.
        :param port: The local port where to receive the data from.
        :param extended_logging: If True the log level will be set to DEBUG
            otherwise to INFO.
        """
        if ip_address is None or port is None:
            self._config = ConfigCat().config

        self.ip_address = ip_address if ip_address else self._config['networking']['source_ip_address']
        self.port = port if port else self._config['networking']['source_port']
        self.data = []
        self.time = []
        self.last_receive_time = 0
        self._extended_logging = extended_logging
        self._sock = None

        LoggingHelper.init_logging(extended_logging)

        self._logger = logging.getLogger(client_name)
        LoggingHelper.init_logger(self._logger, extended_logging)

        # Checking whether save directory exists
        self._save_repository = path.dirname(path.abspath(__file__)) + '/cat_basket'

        if not path.exists(self._save_repository):
            makedirs(self._save_repository)

    def start(self):
        """Create socket and binds to address.

        :return: None
        """
        self._logger.info('Initialize receiver socket to %s:%s', self.ip_address, self.port)

        self._sock = socket(AF_INET, SOCK_DGRAM)
        self._sock.settimeout(self._TIMEOUT)
        self._sock.bind((self.ip_address, self.port))

        self._logger.info('Socket initialized. Bind to %s:%s', self.ip_address, self.port)

    def stop(self):
        """Close the socket.

        :return: None
        """
        self._sock.close()
        self._logger.info('Socket closed.')

    def save_data(self, name=None):
        """Save the data variable to a .npy file.

        :param name: The name of the file, otherwise the current
            timestamp will be used.
        :return: None
        """
        if not name:
            name = time.strftime('%d-%m-%Y__%H-%M-%S', time.localtime())

        data_matrix = np.matrix(self.data)
        time_vector = np.matrix(self.time).transpose()

        full_path = self._save_repository + f'/{name}'

        np.save(full_path, np.hstack((time_vector, data_matrix)))
        self._logger.info('Saved data to %s.', self._save_repository + f'/{name}')

    def receive_data(self):
        """Receive data from Ip address.

        Appends the data variable for each receive.

        :return: The received data
        """
        # self._logger.debug('Receiving data...')
        rec_data = None

        try:
            rec_data_raw, _address = self._sock.recvfrom(self._BUFFER_SIZE)
            received_time = time.time()
            self.last_receive_time = received_time

            # divide by 8 since we need the 64bit double format
            data_size = len(rec_data_raw) / 8
            rec_data = unpack(f'<{int(data_size)}d', rec_data_raw)

            self.data.append(rec_data)
            self.time.append(received_time)

            self._logger.debug('Received %s doubles: %s', data_size, rec_data)
        except timeout:
            self._logger.info('Socket timed out after %s seconds.', self._TIMEOUT)
        except BlockingIOError:
            self._logger.info('Nothing received for %s seconds.', self._TIMEOUT)

        return rec_data
