"""
Generate 8-bit style sound effects for player actions and transitions
"""
import numpy as np
import wave
import struct
import os

def generate_8bit_sfx(filename, frequency_pattern, duration, sample_rate=22050):
    """Generate a simple 8-bit style sound effect"""
    samples = []
    
    for i, (freq, dur) in enumerate(frequency_pattern):
        num_samples = int(sample_rate * dur)
        t = np.linspace(0, dur, num_samples, False)
        
        # Square wave for 8-bit feel
        wave_data = np.sign(np.sin(2 * np.pi * freq * t))
        
        # Add envelope for natural sound
        envelope = np.exp(-3 * t / dur)
        wave_data = wave_data * envelope
        
        samples.extend(wave_data)
    
    # Normalize
    samples = np.array(samples)
    samples = samples * 0.3  # Volume control
    samples = np.int16(samples * 32767)
    
    # Write wav file
    output_path = os.path.join('assets', 'sfx', filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples.tobytes())
    
    print(f"Generated: {output_path}")

def main():
    # Player jump sound (ascending chirp)
    generate_8bit_sfx(
        'player_jump.wav',
        [(440, 0.05), (554, 0.05), (659, 0.05)],
        0.15
    )
    
    # Player defeat sound (descending dramatic)
    generate_8bit_sfx(
        'player_defeat.wav',
        [(659, 0.1), (523, 0.1), (440, 0.1), (349, 0.15), (262, 0.2)],
        0.65
    )
    
    # Victory fanfare (ascending triumph)
    generate_8bit_sfx(
        'victory_fanfare.wav',
        [(523, 0.12), (659, 0.12), (784, 0.12), (1047, 0.25)],
        0.61
    )
    
    # Dandelion float (gentle ascending twinkle)
    generate_8bit_sfx(
        'dandelion_float.wav',
        [(523, 0.15), (587, 0.15), (659, 0.15), (698, 0.2), (784, 0.25)],
        0.9
    )
    
    # Earthquake rumble (low frequency oscillation)
    generate_8bit_sfx(
        'earthquake_rumble.wav',
        [(110, 0.2), (98, 0.2), (110, 0.2), (87, 0.3)],
        0.9
    )
    
    # White fade descent (ethereal descending)
    generate_8bit_sfx(
        'white_fade.wav',
        [(880, 0.2), (784, 0.2), (698, 0.2), (659, 0.3), (587, 0.3)],
        1.2
    )

if __name__ == '__main__':
    main()
