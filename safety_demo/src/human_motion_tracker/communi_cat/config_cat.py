"""This class is used to load the configuration file.

Author:
    Daniil Zauzolkov
Contributor:
    Simon Dobers
    Jakob Thumm
"""

from os import path
import yaml


class ConfigCat:
    """This class is used to load the configuration file.

    :arg config: The configuration dictionary.
    """

    def __init__(self, path_to_config=None):
        """Initialize a class instance and loads the config file.

        :param path_to_config: The path to the config file, else the
            internal config file will be used.

        :raise FileNotFoundError: If internal config file is missing.
        """
        if path_to_config is None:
            path_to_config = path.dirname(path.abspath(__file__)) + '/config.yaml'

            if path.isfile(path_to_config) is False:
                raise FileNotFoundError(
                    f'Configuration file does not exist here {path_to_config}'
                )

        with open(path_to_config) as file:
            self.config = yaml.safe_load(file)
