from enum import Enum


class BallMovements(Enum):
    """
    Pre-defined ball movements
    """

    BALL_STOPPED = 0
    BALL_MOVING = 1
    BALL_ROTATING_LEFT = 2
    BALL_ROTATING_RIGHT = 3
