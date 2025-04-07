# app.py
import os
import librosa
import numpy as np
from flask import Flask, request, jsonify, send_from_directory # Added send_from_directory
from werkzeug.utils import secure_filename
import json # For sending structured data
import soundfile as sf  # Add soundfile for more reliable audio loading

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Limit uploads to 16MB

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to analyze audio
def analyze_audio(filepath):
    try:
        # First try loading with soundfile
        try:
            y, sr = sf.read(filepath)
            # Convert to mono if stereo
            if len(y.shape) > 1:
                y = np.mean(y, axis=1)
        except Exception as e:
            print(f"Soundfile loading failed: {e}, trying librosa")
            # Fallback to librosa if soundfile fails
            y, sr = librosa.load(filepath, sr=None, mono=True)
        
        duration = librosa.get_duration(y=y, sr=sr)

        # --- Feature Extraction ---
        # Define time window for analysis (e.g., ~1 second chunks)
        n_fft = 2048 * 2  # Frame length for FFT
        hop_length = 1024 * 2  # Hop length between frames

        # Calculate features over time windows
        rms_energy = librosa.feature.rms(y=y, frame_length=n_fft, hop_length=hop_length)[0]
        
        # Use librosa's built-in window function
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)[0]
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)

        # Calculate overall BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr) # Simplified BPM estimation

        # Get timestamps for each feature frame
        times = librosa.times_like(rms_energy, sr=sr, hop_length=hop_length)

        # --- Data Structuring ---
        # Normalize features (important for mapping later)
        def normalize(data):
          min_val = np.min(data)
          max_val = np.max(data)
          if max_val == min_val: # Avoid division by zero
              return np.zeros_like(data)
          return (data - min_val) / (max_val - min_val)

        analysis_data = {
            "duration": duration,
            "overall_bpm": float(tempo), # Single value for overall tempo
            "timeline": times.tolist(), # List of timestamps
            "rms_energy": normalize(rms_energy).tolist(),
            "spectral_centroid": normalize(spectral_centroid).tolist(),
            "spectral_bandwidth": normalize(spectral_bandwidth).tolist(),
            # Average chroma features across time for simplicity, or send full matrix if needed
            "chroma_avg": [float(np.mean(c)) for c in normalize(chroma)]
        }
        return analysis_data

    except Exception as e:
        print(f"Error analyzing audio: {e}")
        return None
    finally:
        # Clean up the uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)

# API Endpoint for uploading and analyzing music
@app.route('/analyze', methods=['POST'])
def handle_analysis():
    if 'audioFile' not in request.files:
        return jsonify({"error": "No audio file part"}), 400
    file = request.files['audioFile']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(filepath)
            analysis_results = analyze_audio(filepath) # filepath is now passed
            if analysis_results:
                # Use json.dumps for potentially large data
                return app.response_class(
                    response=json.dumps(analysis_results),
                    status=200,
                    mimetype='application/json'
                )
            else:
                 return jsonify({"error": "Failed to analyze audio"}), 500
        except Exception as e:
             # Clean up if saving failed or analysis raised unexpected error
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Serve the main HTML page (we'll create this in Phase 2)
@app.route('/')
def index():
     # Assumes index.html is in ../frontend relative to app.py
     # Adjust path if your structure is different
    return send_from_directory('frontend', 'index.html')

# Add these two new routes anywhere in app.py (after app = Flask(__name__))
@app.route('/style.css')
def serve_css():
    return send_from_directory('frontend', 'style.css')

@app.route('/sketch.js')
def serve_js():
    return send_from_directory('frontend', 'sketch.js')

if __name__ == '__main__':
    # # Debug=True is helpful during development, remove for production
    # # Host='0.0.0.0' makes it accessible on your network
    # app.run(debug=True, host='0.0.0.0', port=8000)
    # if __name__ == '__main__':
    # Get port from environment variable or default to 5000 for local dev
    port = int(os.environ.get('PORT', 5000))
    # IMPORTANT: Remove debug=True for production!
    # Bind to 0.0.0.0 to accept connections from outside the container
    app.run(host='0.0.0.0', port=port)

