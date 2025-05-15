# sound_manager.py
# This file handles sound generation and management for the Rally Racer game.

import numpy as np
import math
# Assuming constants.py is in the parent directory or the project root is in PYTHONPATH
# If running main.py from the project root, this import should work.
from constants import SAMPLE_RATE # Only import what's needed

def generate_sound_array(freq, duration_ms, waveform='sine', sample_rate=SAMPLE_RATE):
    """
    Generates a NumPy array representing a sound wave.

    Args:
        freq (float): Frequency of the sound in Hz. For noise, this can be 0.
        duration_ms (int): Duration of the sound in milliseconds.
        waveform (str, optional): Type of waveform ('sine', 'square', 'noise', 'engine'). 
                                  Defaults to 'sine'.
        sample_rate (int, optional): Samples per second. Defaults to SAMPLE_RATE from constants.

    Returns:
        numpy.ndarray: A 2D NumPy array representing the stereo sound data, 
                       formatted for Pygame's Sound constructor.
    """
    # Calculate the number of samples
    num_samples = int(sample_rate * duration_ms / 1000.0)
    if num_samples <= 0:
        # Return a very short silent array if duration is too small or zero
        return np.zeros((1, 2), dtype=np.int16)

    # Create a time array from 0 to duration_ms (in seconds)
    t = np.linspace(0., duration_ms / 1000., num_samples, endpoint=False)

    wave = None # Initialize wave

    if waveform == 'sine':
        # Sine wave: 0.5 amplitude to prevent clipping when converting to int16
        wave = 0.5 * np.sin(2. * math.pi * freq * t)
    elif waveform == 'square':
        # Square wave
        wave = 0.5 * np.sign(np.sin(2. * math.pi * freq * t))
    elif waveform == 'noise':
        # White noise: random values between -0.5 and 0.5
        wave = np.random.uniform(-0.5, 0.5, len(t))
    elif waveform == 'engine': # Sawtooth-like wave for a basic engine sound
        # This creates a waveform that rises linearly and then drops, repeating.
        # The frequency here controls the pitch of the "putt-putt" sound.
        # The 0.4 amplitude keeps it from being too harsh.
        if freq <= 0: # Avoid division by zero or negative frequencies for engine
            wave = np.zeros(len(t)) # Silent if frequency is invalid for engine
        else:
            period = sample_rate / freq
            wave = 0.4 * ( (t * sample_rate) % period / period * 2.0 - 1.0)
            # A simpler sawtooth: wave = 0.4 * (t * freq - np.floor(t * freq + 0.5))

    else: # Default to sine wave if waveform is unrecognized
        print(f"Warning: Unrecognized waveform '{waveform}'. Defaulting to sine.")
        wave = 0.5 * np.sin(2. * math.pi * freq * t)
    
    if wave is None: # Should not happen if logic is correct, but as a fallback
        wave = np.zeros(len(t))

    # Convert to 16-bit integers (Pygame's preferred format for Sound objects)
    # Scale by 32767 (max value for int16)
    sound_array_mono = np.int16(wave * 32767)

    # Create a stereo array by duplicating the mono channel
    # Pygame Sound objects expect a 2D array (num_samples, num_channels)
    # Using np.ascontiguousarray can sometimes help with Pygame buffer issues.
    sound_array_stereo = np.ascontiguousarray(np.vstack((sound_array_mono, sound_array_mono)).T)
    
    return sound_array_stereo

# You could add more sound management functions here later, for example:
# - A function to load sounds from files if you add sound assets
# - Functions to manage sound channels or groups
# - Functions to play sounds with variations (pitch, volume)
