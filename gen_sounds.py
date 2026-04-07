import wave
import struct
import math

def generate_beep(filename, duration=0.1, freq=880, volume=0.5, sample_rate=44100):
    num_samples = int(duration * sample_rate)
    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        for i in range(num_samples):
            value = int(volume * 32767.0 * math.sin(2.0 * math.pi * freq * i / sample_rate))
            data = struct.pack('<h', value)
            f.writeframesraw(data)

def generate_simple_bgm(filename, duration=10, volume=0.2, sample_rate=44100):
    num_samples = int(duration * sample_rate)
    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        
        # Simple arpeggio melody
        notes = [261.63, 329.63, 392.00, 523.25] # C4, E4, G4, C5
        note_duration = 0.5
        samples_per_note = int(note_duration * sample_rate)
        
        for i in range(num_samples):
            note_idx = (i // samples_per_note) % len(notes)
            freq = notes[note_idx]
            value = int(volume * 32767.0 * math.sin(2.0 * math.pi * freq * i / sample_rate))
            data = struct.pack('<h', value)
            f.writeframesraw(data)

if __name__ == "__main__":
    generate_beep("score.wav")
    generate_simple_bgm("background.wav")
