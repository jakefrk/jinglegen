import os
from flask import Flask, request, render_template, jsonify
import librosa
import numpy as np
from datetime import datetime
import time

# --- Flask App Setup ---
app = Flask(__name__)
# Configure a directory to temporarily store uploaded files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Create the folder if it doesn't exist
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Your Core Audio Analysis Logic ---
def analyze_audio(file_path):
    """Extract detailed audio features using librosa"""
    print(f"[{time.strftime('%H:%M:%S')}] Starting analysis for: {file_path}")
    start_time = time.time()

    try:
        print(f"[{time.strftime('%H:%M:%S')}] Loading audio...")
        load_start = time.time()
        # Process max 15 seconds
        y, sr = librosa.load(file_path, duration=15.0)
        print(f"[{time.strftime('%H:%M:%S')}] Audio loaded in {time.time() - load_start:.2f}s. Sample rate: {sr}, Duration of y: {len(y)/sr:.2f}s")

        # Mood/Energy Analysis
        print(f"[{time.strftime('%H:%M:%S')}] Calculating spectral rolloff...")
        rolloff_start = time.time()
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
        print(f"[{time.strftime('%H:%M:%S')}] Spectral rolloff calculated in {time.time() - rolloff_start:.2f}s.")

        print(f"[{time.strftime('%H:%M:%S')}] Calculating spectral bandwidth...")
        bandwidth_start = time.time()
        spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
        print(f"[{time.strftime('%H:%M:%S')}] Spectral bandwidth calculated in {time.time() - bandwidth_start:.2f}s.")

        # Instrument Analysis
        print(f"[{time.strftime('%H:%M:%S')}] Performing HPSS...")
        hpss_start = time.time()
        harmonic, percussive = librosa.effects.hpss(y)
        print(f"[{time.strftime('%H:%M:%S')}] HPSS completed in {time.time() - hpss_start:.2f}s.")
        
        harmonic_sum = np.mean(harmonic) # These np.mean calls should be very fast
        percussive_sum = np.mean(percussive)
        if harmonic_sum + percussive_sum == 0:
            harmonic_ratio = 0.5
        else:
            harmonic_ratio = harmonic_sum / (harmonic_sum + percussive_sum)
        print(f"[{time.strftime('%H:%M:%S')}] Harmonic ratio calculated.")

        # Musical Characteristics
        print(f"[{time.strftime('%H:%M:%S')}] Calculating onset strength...")
        onset_env_start = time.time()
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        print(f"[{time.strftime('%H:%M:%S')}] Onset strength calculated in {time.time() - onset_env_start:.2f}s.")

        print(f"[{time.strftime('%H:%M:%S')}] Tracking beat...")
        beat_track_start = time.time()
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        print(f"[{time.strftime('%H:%M:%S')}] Beat tracked in {time.time() - beat_track_start:.2f}s. Tempo: {tempo}")

        # Rhythm Analysis
        print(f"[{time.strftime('%H:%M:%S')}] Detecting onsets...")
        onset_detect_start = time.time()
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        print(f"[{time.strftime('%H:%M:%S')}] Onsets detected in {time.time() - onset_detect_start:.2f}s. Count: {len(onset_frames)}")
        
        audio_duration_seconds = len(y) / sr # Fast
        if audio_duration_seconds == 0:
            rhythm_density = 0
        else:
            rhythm_density = len(onset_frames) / audio_duration_seconds
        print(f"[{time.strftime('%H:%M:%S')}] Rhythm density calculated.")

        raw_analysis_results = {
            'mood_energy': {
                'spectral_rolloff': float(spectral_rolloff),
                'spectral_bandwidth': float(spectral_bandwidth),
                'interpreted_energy': 'High' if spectral_rolloff > 3000 else 'Medium' if spectral_rolloff > 1500 else 'Low',
                'interpreted_brightness': 'Bright' if spectral_bandwidth > 2000 else 'Muted'
            },
            'instrument_analysis': {
                'harmonic_ratio': float(harmonic_ratio),
                'harmonic_energy_mean': float(harmonic_sum),
                'percussive_energy_mean': float(percussive_sum),
                'interpreted_instrument_type': 'Melodic' if harmonic_ratio > 0.6 else 'Percussive' if harmonic_ratio < 0.4 else 'Mixed'
            },
            'musical_characteristics': {
                'tempo_bpm': int(tempo) if tempo else 0,
                'onset_strength_mean': float(np.mean(onset_env)),
                'interpreted_style': 'Fast-paced' if tempo and tempo > 120 else 'Medium-paced' if tempo and tempo > 90 else 'Slow-paced'
            },
            'rhythm_analysis': {
                'onset_count': len(onset_frames),
                'rhythm_density_onsets_per_sec': float(rhythm_density),
                'interpreted_beat_density': 'High' if rhythm_density > 2 else 'Medium' if rhythm_density > 1 else 'Low'
            }
        }
        print(f"[{time.strftime('%H:%M:%S')}] Analysis dictionary populated.")
        total_time = time.time() - start_time
        print(f"[{time.strftime('%H:%M:%S')}] Total analysis time: {total_time:.2f}s")
        return raw_analysis_results

    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error during audio analysis: {e}")
        # Also log the full traceback to the terminal for more details
        import traceback
        traceback.print_exc() 
        return {"error": str(e), "trace": traceback.format_exc()}

# --- ORTB Request Generation (Python version) ---
def generate_ortb_request_py(raw_audio_analysis_data, transcribed_text=""):
    """Generate a mock ORTB bid request with selected audio signals (Python version)"""
    
    ortb_signals = {
        "energy_level": raw_audio_analysis_data.get('mood_energy', {}).get('interpreted_energy', 'N/A'),
        "brightness": raw_audio_analysis_data.get('mood_energy', {}).get('interpreted_brightness', 'N/A'),
        "instrument_type": raw_audio_analysis_data.get('instrument_analysis', {}).get('interpreted_instrument_type', 'N/A'),
        "tempo_bpm": raw_audio_analysis_data.get('musical_characteristics', {}).get('tempo_bpm', 0),
        "style": raw_audio_analysis_data.get('musical_characteristics', {}).get('interpreted_style', 'N/A'),
        "beat_density": raw_audio_analysis_data.get('rhythm_analysis', {}).get('interpreted_beat_density', 'N/A'),
        "onset_count": raw_audio_analysis_data.get('rhythm_analysis', {}).get('onset_count', 0)
    }
    if transcribed_text:
        ortb_signals["transcribed_text_snippet"] = transcribed_text[:256]

    return {
        "id": f"bid-local-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "imp": [{
            "id": "1",
            "audio": {
                "mimes": ["audio/mpeg", "audio/wav"], 
                "minduration": 1,
                "maxduration": 5,
            },
            "ext": {
                "custom_audio_signals": ortb_signals 
            }
        }],
        "app": {
            "id": "jinglegen-app-v1-local",
            "name": "JingleGen Audio Analyzer (Local Demo)",
            "bundle": "com.example.jinglegen.local",
            "publisher": {
                "id": "pub-local-12345",
                "name": "JingleGen Publisher (Local)"
            }
        },
        "device": { 
            "ua": "LocalTestClient/1.0", 
            "ip": "127.0.0.1",
            "devicetype": 2 
        },
        "user": {
            "id": f"local-user-api-{datetime.now().strftime('%S%f')}"
        },
        "at": 1, 
        "tmax": 200,
        "regs": {
            "coppa": 0,
            "ext": { "gdpr": 0 }
        }
    }

# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_audio_route():
    """Handles audio file uploads and triggers analysis."""
    if 'audioFile' not in request.files:
        return jsonify({"error": "No audio file part in the request"}), 400
    
    file = request.files['audioFile']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        filename = file.filename 
        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(temp_file_path)
            
            raw_analysis_results = analyze_audio(temp_file_path)
            ortb_bid_request = generate_ortb_request_py(raw_analysis_results, transcribed_text="") 
            
            combined_results = {
                "audio_analysis": raw_analysis_results,
                "ortb_request": ortb_bid_request
            }
            
            return jsonify(combined_results)
            
        except Exception as e:
            print(f"Error processing file: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Server error processing file: {e}", "trace": traceback.format_exc()}), 500
        finally:
            if os.path.exists(temp_file_path):
                # os.remove(temp_file_path) 
                pass
    
    return jsonify({"error": "File processing failed"}), 500

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True, port=5000) # Runs the Flask development server
