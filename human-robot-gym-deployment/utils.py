import os

def get_config_path():
    """
    Get system-dependent absolute path for the config file in the human-robot-gym-ss-23 repository.
    """
    # The following lines are written to obtain the config path of the training repository.
    # Get path to the folder in which this file is
    dir_path = os.path.dirname(os.path.realpath(__file__))
    print('dir_path: {}'.format(dir_path))

    # Get path to folder in which this project is
    dir_path = os.path.dirname(dir_path)
    print('dir_path: {}'.format(dir_path))
    # This code assumes that the deployment and training repos are in the same folder
    config_path = dir_path + "/human-robot-gym-ss-23/human_robot_gym/training/config"

    # Assert that the human-robot-gym-ss-23 repository from the config file has already been cloned
    error_message = "You need to clone our training repository human-robot-gym-ss-23 as well."
    assert os.path.exists(dir_path + "/human-robot-gym-ss-23"), error_message
    return config_path