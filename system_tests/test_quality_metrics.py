"""
This file contains the data collection for quality metrics related to the
system.
"""

import pytest
from math import sqrt, pow
from datetime import datetime, timedelta
import os
from fake_data.scenarios import (
    SCENARIOS_2D,
    SCENARIOS_3D
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from fake_data.generate_differences import Scenario


@pytest.mark.skip  # Not implemented
def test_2d_error():
    """
    Id: 1
    Quality requirement: 3.5.2
    Dependencies: This test requires that atleast one method for locating
    sounds has been implemented.
    Tests: This test collects metrics on the margin of error when locating
    sounds in two dimensions.
    """
    folders = os.listdir("fake_data/audio_2d")
    assert len([0 for scenario, folder in zip(SCENARIOS_2D, folders) if
                within_2d_error(scenario, folder)]) / len(folders) >= 0.8


@pytest.mark.skip  # Not implemented
def test_3d_error():
    """
    Id: 2
    Quality requirement: 3.5.4
    Dependencies: This test requires that atleast one method for locating
    sounds has been implemented. It also requires the system pipeline is
    implemented in order to correctly measure the delay between data input to
    data output.
    Tests: This test collects metrics on the total delay from inputted sounds
    to outputted position.
    """
    folders = os.listdir("fake_data/audio_3d")
    assert len([0 for scenario, folder in zip(SCENARIOS_3D, folders) if
                within_3d_error(scenario, folder)]) / len(folders) >= 0.75


@pytest.mark.skip  # Not implemented
def test_delay():
    """
    Id: 3
    Quality requirement: 3.5.3
    Dependencies: This test requires that atleast one method for locating
    sounds has been implemented.
    Tests: This test collects metrics on the margin of error when locating
    sounds in three dimensions. This in relation to a horizontal x and y
    plane, as well as a vertical axis z.
    """
    folders = (os.listdir("fake_data/audio_2d") +
               os.listdir("fake_data/audio_3d"))
    assert len([0 for folder in folders if
                within_allowed_time(folder)]) / len(folders) >= 0.8

# Helper functions


def distance(source: tuple[float, float, float],
             guess: tuple[float, float, float]):
    """
    Checks distance between a source of a sound and a guess.
    """
    return sqrt(pow(source[0] - guess[0], 2) +
                pow(source[1] - guess[1], 2) +
                pow(source[2] - guess[2], 2))


def within_2d_error(scenario: Scenario, folder: str):
    """
    Quality requirement: 3.5.2
    Verifies that a guessed postion is within the allowed margin of error for
    the 2d plane.
    """
    source = scenario.sender
    # audio_files = os.listdir(folder)
    # TODO: guess = guess_pos(data)
    guess = (0, 0, 0)  # TODO: temp replace with actual guess above.
    microphone_distance = scenario.receivers[0].distance(scenario.receivers[1])
    source_no_z = (source.x, source.y, 0)
    guess_no_z = (guess[0], guess[1], 0)
    return distance(source_no_z, guess_no_z) <= microphone_distance * 0.2


def within_3d_error(scenario: Scenario, folder: str):
    """
    Quality requirement: 3.5.4
    Verifies that a guessed postion is within the allowed margin of error for
    three dimensions.
    """
    source = (scenario.sender.x, scenario.sender.y, scenario.sender.z)
    # audio_files = os.listdir(folder)
    # TODO: guess = guess_pos(data)
    guess = (0, 0, 0)  # TODO: temp replace with actual guess above.
    return distance(source, guess) <= 5


def within_allowed_time(folder: str):
    """
    Quality requirement: 3.5.3
    Verifies that a answer is given within the allowed time.
    """
    start = datetime.now()
    # audio_files = os.listdir(folder)
    # TODO: guess_pos(data) # perform guess
    return datetime.now() - start <= timedelta(seconds=0.5)


if __name__ == "__main__":
    # When collecting metrics this is run instead of the pytest tests.
    folders_2d = os.listdir("fake_data/audio_2d")
    folders_3d = os.listdir("fake_data/audio_3d")
    folders = folders_2d + folders_3d

    pass_2d_percentage = len(
        [0 for scenario, folder in zip(SCENARIOS_2D, folders_2d) if
         within_2d_error(scenario, folder)]) / len(folders_2d) * 100
    pass_3d_percentage = len(
        [0 for scenario, folder in zip(SCENARIOS_3D, folders_3d) if
         within_3d_error(scenario, folder)]) / len(folders_3d) * 100
    pass_delay_percentage = (len(
        [0 for folder in folders if within_allowed_time(folder)]) /
        len(folders) * 100)

    print(f"Within 20% of the distance between microphones in a 2d plane, {
          pass_2d_percentage}% of the time.")
    print(f"Within 5 meters in a 3d space, {pass_3d_percentage}% of the time.")
    print(f"Gives a postion withing 0.5s, {
          pass_delay_percentage}% of the time.")
