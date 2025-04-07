# Generative Bliss Scape

A web application that transforms uploaded music into mesmerizing, abstract visual experiences, designed to help users relax and enter a "blissful" state. Features dynamically forming shapes based on the music's characteristics.


## Features

*   **Audio Upload:** Accepts common audio file formats.
*   **AI Music Analysis:** Extracts features like energy (RMS), spectral centroid (brightness), spectral bandwidth (richness), and overall tempo (BPM) using Librosa.
*   **Dynamic Generative Visuals:** Utilizes p5.js to create a constantly evolving particle system (flow field).
*   **Shape Formation:** Particles periodically attempt to form outlines of recognizable shapes (e.g., Smiley, Heart, Eiffel Tower, Diamond, Globe) based on musical triggers and timing.
*   **Synchronized Audio Playback:** Plays the uploaded audio in sync with the visuals using HTML5 Audio.
*   **Web Interface:** Simple UI for file upload and status updates.
*   **Progress Indication:** Shows upload progress.

## Technology Stack

*   **Backend:**
    *   Python 3
    *   Flask (Web framework)
    *   Librosa (Audio analysis)
    *   NumPy (Numerical operations)
    *   SoundFile (Audio file loading)
    *   Gunicorn (Production WSGI server)
*   **Frontend:**
    *   HTML5
    *   CSS3
    *   JavaScript
    *   p5.js (Creative coding library for visuals)

## Setup and Running Locally

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd bliss_scape
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    # Create venv
    python -m venv venv

    # Activate venv
    # macOS / Linux:
    source venv/bin/activate
    # Windows:
    # .\venv\Scripts\activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(This may take a few minutes, especially for libraries like SciPy/Librosa).*

4.  **Run the Flask development server:**
    ```bash
    python app.py
    ```

5.  **Access the application:** Open your web browser and go to `http://127.0.0.1:5000` (or the address provided in the terminal, usually port 5000 when running locally with `app.py`).

## Usage

1.  Open the application URL in your browser.
2.  Click the "Choose File" button and select an audio file (e.g., MP3, WAV).
3.  Click the "Generate Bliss" button.
4.  The application will show upload progress, then analyze the audio (this might take a moment depending on file size and server performance).
5.  Once analysis is complete, the audio will start playing, and the visuals will react and form shapes based on the music.

## Deployment

This application is configured for deployment on Platform-as-a-Service (PaaS) providers like [Render](https://render.com/).

*   **`requirements.txt`**: Lists all necessary Python packages for `pip install`.
*   **`Procfile`**: Tells the platform how to start the web server using `gunicorn`.
*   **Relative Paths**: The frontend `fetch` request uses a relative path (`/analyze`), which works correctly when Flask serves both the frontend and backend from the same origin, as configured for Render deployment in the instructions.

Follow the deployment guide for your chosen platform (e.g., Render's "Deploy a Python Flask App" guide), connecting it to your Git repository.

## Future Ideas

*   More sophisticated shape generation and triggering logic based on deeper musical analysis (e.g., mood, genre).
*   Smoother transitions between FLOW and SEEK behaviors for particles.
*   User controls for visual parameters (colors, particle count, shape frequency).
*   More diverse visual modes beyond particle systems.
*   Performance optimizations for handling larger audio files or more complex visuals.

## Motivation

Built with the intention of sharing the joy and immersive feeling that music can bring through interactive visual art. Just want people smiling!
