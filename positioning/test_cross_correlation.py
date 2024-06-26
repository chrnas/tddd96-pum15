import numpy as np
import pytest
from .cross_correlation import create_wav_object, calc_shifted_samples_fft


@pytest.fixture
def example_wavfile():
    """
    Fixture to create a WavFile object for testing.
    """
    # Create a WavFile object with dummy data
    audio_data = np.sin(2 * np.pi * np.linspace(0, 1, 48000))
    sample_rate = 48000
    wav_file = create_wav_object(audio_data, sample_rate)
    return wav_file


def test_audio_data_size(example_wavfile):
    """
    Test if audio_data_size method returns the correct size.
    """
    assert example_wavfile.audio_data_size(
    ) == 48000, "Audio data size should be equal to 48000"


def test_resample_wav(example_wavfile):
    """
    Test if resample_wav method correctly changes the sampling rate.
    """
    example_wavfile.resample_wav(24000)
    assert example_wavfile.sampling_rate == 24000, "Sampling rate should be updated to 24000"
    # Note: This test does not check if the data was correctly resampled, just the sample rate change.


def test_calc_shifted_samples_fft():
    """
    Test calculation of shifted samples using FFT with identical files.
    """
    # Create two identical WavFile objects for testing
    audio_data = np.sin(2 * np.pi * np.linspace(0, 1, 48000))
    sample_rate = 48000
    wav_file1 = create_wav_object(audio_data, sample_rate)
    wav_file2 = create_wav_object(audio_data, sample_rate)
    assert calc_shifted_samples_fft(
        wav_file1, wav_file2) == 0, "Shifted samples should be 0 for identical audio"
