import os
import librosa
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import json
import soundfile as sf
import traceback # For better error logging

# Define a target sample rate to reduce memory/CPU load
TARGET_SR = 22050

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Keep upload limit reasonable, analysis is the bottleneck
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to normalize features
def normalize(data):
    min_val = np.min(data)
    max_val = np.max(data)
    if max_val == min_val:
        return np.zeros_like(data)
    return (data - min_val) / (max_val - min_val)

# Function to analyze audio (modified for lower SR)
def analyze_audio(filepath):
    y = None
    sr = TARGET_SR # Assume target SR initially
    try:
        print(f"Analyzing file: {filepath}") # Log start

        # --- Optimized Audio Loading ---
        try:
            # Try loading with soundfile first
            data, orig_sr = sf.read(filepath, dtype='float32', always_2d=False)
            print(f"Loaded with soundfile. Original SR: {orig_sr}, Shape: {data.shape}")

            # Convert to mono
            if len(data.shape) > 1 and data.shape[-1] > 1: # Check if stereo
                 print("Converting to mono...")
                 y = np.mean(data, axis=-1)
            else:
                 y = data

            # Resample if necessary
            if orig_sr != TARGET_SR:
                print(f"Resampling from {orig_sr} to {TARGET_SR}...")
                y = librosa.resample(y=y, orig_sr=orig_sr, target_sr=TARGET_SR)
                sr = TARGET_SR
                print(f"Resampling complete. New shape: {y.shape}")
            else:
                sr = orig_sr # Use original if it matches target

        except Exception as e_sf:
            print(f"Soundfile loading/processing failed: {e_sf}. Falling back to librosa loading directly at TARGET_SR.")
            # Fallback to librosa loading directly at target SR
            # This is often more memory efficient than loading high-SR then resampling
            try:
                 y, sr = librosa.load(filepath, sr=TARGET_SR, mono=True)
                 print(f"Loaded with librosa at {sr} Hz. Shape: {y.shape}")
            except Exception as e_librosa:
                print(f"Librosa loading also failed: {e_librosa}")
                raise RuntimeError(f"Failed to load audio with both soundfile and librosa: {e_librosa}") from e_librosa


        # --- Feature Extraction (using potentially downsampled y and sr) ---
        if y is None or len(y) == 0:
             raise ValueError("Audio data 'y' is empty after loading.")

        print("Calculating duration...")
        # Use the loaded data which might be shorter due to resampling
        duration = librosa.get_duration(y=y, sr=sr)
        print(f"Duration: {duration:.2f}s")

        # Define analysis parameters
        n_fft = 2048 # Smaller FFT might be slightly less precise but faster/less memory
        hop_length = int(n_fft / 2) # Standard overlap

        print("Calculating RMS energy...")
        rms_energy = librosa.feature.rms(y=y, frame_length=n_fft, hop_length=hop_length)[0]

        print("Calculating spectral centroid...")
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)[0]

        print("Calculating spectral bandwidth...")
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)[0]

        # Chroma might still be relatively expensive
        print("Calculating chroma features...")
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)

        # Tempo calculation can also be expensive
        print("Calculating tempo...")
        try:
            # Use default units (BPM)
            tempo_value = librosa.beat.tempo(y=y, sr=sr)[0]
            print(f"Tempo estimated: {tempo_value:.2f} BPM")
        except Exception as e_beat:
            print(f"Tempo estimation failed: {e_beat}, defaulting BPM to 120")
            tempo_value = 120.0

        print("Generating timeline...")
        times = librosa.times_like(rms_energy, sr=sr, hop_length=hop_length)

        # --- Data Structuring ---
        print("Structuring and normalizing data...")
        analysis_data = {
            "duration": duration,
            "overall_bpm": float(tempo_value),
            "timeline": times.tolist(),
            "rms_energy": normalize(rms_energy).tolist() if np.any(rms_energy) else np.zeros_like(rms_energy).tolist(),
            "spectral_centroid": normalize(spectral_centroid).tolist() if np.any(spectral_centroid) else np.zeros_like(spectral_centroid).tolist(),
            "spectral_bandwidth": normalize(spectral_bandwidth).tolist() if np.any(spectral_bandwidth) else np.zeros_like(spectral_bandwidth).tolist(),
            "chroma_avg": [float(np.mean(c)) for c in normalize(chroma)] if np.any(chroma) else [0.0]*12
        }
        print("Analysis complete.")
        return analysis_data

    except Exception as e:
        print(f"ERROR during audio analysis: {e}")
        traceback.print_exc() # Print detailed traceback to logs
        return None # Indicate failure
    finally:
        # Clean up the uploaded file reliably
        if 'filepath' in locals() and os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"Removed temporary file: {filepath}")
            except OSError as e_remove:
                 print(f"Error removing temporary file {filepath}: {e_remove}")


# --- Flask Routes (Keep as before) ---

@app.route('/analyze', methods=['POST'])
def handle_analysis():
    # ... (Keep file check logic as before) ...
    if 'audioFile' not in request.files: return jsonify({"error": "No audio file part"}), 400
    file = request.files['audioFile']
    if file.filename == '': return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        # Ensure uploads directory exists (Flask might run from different relative paths)
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        print(f"Saving uploaded file to: {filepath}")

        try:
            file.save(filepath)
            print(f"File saved. Starting analysis...")
            analysis_results = analyze_audio(filepath) # Call the modified function

            if analysis_results:
                print("Analysis successful. Sending results.")
                return app.response_class(
                    response=json.dumps(analysis_results),
                    status=200,
                    mimetype='application/json'
                )
            else:
                 print("Analysis failed (returned None). Sending error.")
                 # Error details should have been logged in analyze_audio
                 return jsonify({"error": "Failed during audio analysis process."}), 500
        except Exception as e:
             print(f"ERROR during /analyze request handling: {e}")
             traceback.print_exc() # Log the exception
             # Clean up file if save succeeded but analysis call failed
             if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"Removed temporary file after exception: {filepath}")
                except OSError as e_remove:
                     print(f"Error removing file {filepath} after exception: {e_remove}")
             return jsonify({"error": f"An internal server error occurred."}), 500
        # Note: The finally block in analyze_audio handles cleanup if analysis starts

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/style.css')
def serve_css():
    return send_from_directory('frontend', 'style.css')

@app.route('/sketch.js')
def serve_js():
    return send_from_directory('frontend', 'sketch.js')

# --- Main Execution Block (Keep as before for production/Render) ---
if __name__ == '__main__':
    # Get port from environment variable or default to 5000 for local dev
    # Render sets the PORT env var, Gunicorn uses this host/port binding
    port = int(os.environ.get('PORT', 5000))
    # Run directly only for local testing (Gunicorn is used in Procfile for Render)
    # Set debug=False for any non-Gunicorn run testing production behavior
    print(f"Starting Flask app locally on host 0.0.0.0 port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)