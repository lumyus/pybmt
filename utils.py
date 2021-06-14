import yaml

from enum import Enum


class BallMovements(Enum):
    """
    Pre-defined ball movements
    """

    BALL_STOPPED = 0
    BALL_MOVING = 1
    BALL_ROTATING_LEFT = 2
    BALL_ROTATING_RIGHT = 3


def read_yaml(file_path):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)

