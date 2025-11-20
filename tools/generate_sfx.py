import wave
import math
import random
import struct
import os

def generate_wav(filename, duration, func, volume=0.5, sample_rate=44100):
    """
    Generates a mono WAV file.
    func(t) should return a value between -1.0 and 1.0, where t is time in seconds.
    """
    n_samples = int(duration * sample_rate)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with wave.open(filename, 'w') as w:
        w.setnchannels(1)      # Mono
        w.setsampwidth(2)      # 16-bit
        w.setframerate(sample_rate)
        
        data = []
        for i in range(n_samples):
            t = i / sample_rate
            val = func(t)
            # Clip
            val = max(-1.0, min(1.0, val))
            # Scale to 16-bit integer
            sample = int(val * 32767.0 * volume)
            data.append(struct.pack('<h', sample))
            
        w.writeframes(b''.join(data))
    print(f"Generated {filename}")

# --- Sound Synthesis Functions ---

def noise(t):
    return random.uniform(-1, 1)

def sine(t, freq):
    return math.sin(2 * math.pi * freq * t)

def saw(t, freq):
    return 2 * (t * freq - math.floor(t * freq + 0.5))

def square(t, freq):
    return 1.0 if sine(t, freq) >= 0 else -1.0

# --- Specific SFX Generators ---

def sfx_shoot(t):
    # Pitch drop: 800Hz -> 200Hz
    freq = 800 - 1600 * t
    if freq < 100: freq = 100
    return square(t, freq) * (1.0 - t/0.3) # Decay

def sfx_hit(t):
    # Noise burst with decay
    return noise(t) * (1.0 - t/0.2)**2

def sfx_sloth_slime(t):
    # Wobbly low sine
    freq = 300 + 100 * math.sin(t * 50)
    return sine(t, freq) * (1.0 - t/0.4)

def sfx_sloth_dash(t):
    # Low noise sweep
    return noise(t) * 0.8 * math.sin(t * math.pi / 0.6)

def sfx_sloth_charge(t):
    # Rising pitch
    freq = 100 + 600 * t
    return saw(t, freq) * 0.6

def sfx_sloth_impact(t):
    # Low freq boom + noise
    base = sine(t, 60) * (1.0 - t/0.8)
    crash = noise(t) * (1.0 - t/0.4)**3
    return (base + crash) * 0.8

def sfx_hollow_teleport(t):
    # Rapid random pitch changes (glitchy)
    freq = random.choice([400, 800, 1200])
    return square(t, freq) * (1.0 - t/0.3)

def sfx_hollow_shoot(t):
    # High pitch laser chirp
    freq = 1200 - 2000 * t
    if freq < 200: freq = 200
    return saw(t, freq) * (1.0 - t/0.2)

def sfx_hollow_rain(t):
    # Ethereal shimmer
    v1 = sine(t, 800)
    v2 = sine(t, 805) # beat freq
    return (v1 + v2) * 0.5 * (1.0 - t/1.5)

def main():
    base_path = os.path.join('assets', 'sfx')
    
    # Common
    generate_wav(os.path.join(base_path, 'player_shoot.wav'), 0.2, sfx_shoot, 0.3)
    generate_wav(os.path.join(base_path, 'hit.wav'), 0.2, sfx_hit, 0.4)
    
    # Sloth
    generate_wav(os.path.join(base_path, 'sloth_slime.wav'), 0.4, sfx_sloth_slime, 0.5)
    generate_wav(os.path.join(base_path, 'sloth_dash.wav'), 0.6, sfx_sloth_dash, 0.6)
    generate_wav(os.path.join(base_path, 'sloth_charge.wav'), 1.0, sfx_sloth_charge, 0.4)
    generate_wav(os.path.join(base_path, 'sloth_impact.wav'), 0.8, sfx_sloth_impact, 0.8)
    
    # Hollow
    generate_wav(os.path.join(base_path, 'hollow_teleport.wav'), 0.3, sfx_hollow_teleport, 0.4)
    generate_wav(os.path.join(base_path, 'hollow_shoot.wav'), 0.2, sfx_hollow_shoot, 0.3)
    generate_wav(os.path.join(base_path, 'hollow_rain.wav'), 1.5, sfx_hollow_rain, 0.4)

if __name__ == '__main__':
    main()
