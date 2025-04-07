// --- Visual Modes ---
const VIBE = {
    UNKNOWN: 'UNKNOWN',
    CALM: 'CALM',
    GROOVY: 'GROOVY',
    ENERGETIC: 'ENERGETIC',
    INTENSE: 'INTENSE'
};
let currentVisualMode = VIBE.UNKNOWN;
let lastVibeCheckTime = 0;
const VIBE_CHECK_INTERVAL = 200; // Milliseconds between checking vibe

// --- Shared Visual Elements & Parameters ---
let particles = []; // Can be repurposed or managed per mode
const MAX_PARTICLES = 500; // Increase max potential particles
let transitionProgress = 0; // For fading between modes (0 to 1)
let transitioning = false;
let oldVisualMode = VIBE.UNKNOWN;

// --- Mode-Specific Parameters (Examples) ---
// Calm
let calmCloudOffset = 0;
// Groovy
let groovyOrbits = [];
// Energetic
let energyPulses = [];
let lastEnergyPeakTime = 0;
// Intense
let glitchAmount = 0;

// --- Base Music Parameters (Updated in updateVisualsFromMusic) ---
let currentEnergy = 0.1;
let currentCentroid = 0.5;
let currentBandwidth = 0.3;
let currentBPM = 120;
let currentHue = 180;
let currentSaturation = 80;
let currentBrightness = 100; // Max brightness for base elements

// --- Audio and UI Elements ---
let audioPlayer;
let uploadProgress;
let statusMsg;

// --- Music Data Handling ---
let musicData = null;
let currentDataIndex = 0;

// =============================================================
// SETUP
// =============================================================
function setup() {
    let canvasContainer = document.getElementById('canvas-container');
    let canvas = createCanvas(canvasContainer.offsetWidth, canvasContainer.offsetHeight);
    canvas.parent('canvas-container');
    colorMode(HSB, 360, 100, 100, 100);
    background(0);

    audioPlayer = document.getElementById('audioPlayer');
    uploadProgress = document.getElementById('uploadProgress');
    statusMsg = document.getElementById('statusMessage');

    // Initialize particle array (can grow up to MAX_PARTICLES)
    particles = [];

    initializeUploadListener();
    currentVisualMode = VIBE.CALM; // Start calm before music
    oldVisualMode = VIBE.CALM;
    initializeMode(currentVisualMode); // Set up initial mode visuals
}

// =============================================================
// DRAW LOOP
// =============================================================
function draw() {
    // Always have a very slow fade to clear old frames
    background(0, 0, 0, 3); // Even more subtle fade

    if (musicData) {
        updateMusicAnalysis(); // Update global music parameters & check vibe
    } else {
        // Default behavior when no music is playing (e.g., slow calm mode)
        currentEnergy = lerp(currentEnergy, 0.1, 0.05); // Fade parameters down
        currentCentroid = lerp(currentCentroid, 0.5, 0.05);
        currentBandwidth = lerp(currentBandwidth, 0.3, 0.05);
        determineCurrentVibe(true); // Force calm if no music
    }

     handleTransition(); // Handle fade between modes if transitioning

    // Call the drawing function for the current mode(s)
    if (transitioning) {
        drawMode(oldVisualMode, 1 - transitionProgress); // Draw old mode fading out
        drawMode(currentVisualMode, transitionProgress); // Draw new mode fading in
    } else {
        drawMode(currentVisualMode, 1.0); // Draw current mode fully
    }

}

// =============================================================
// MODE DRAWING ROUTER
// =============================================================
function drawMode(mode, alphaMultiplier) {
     // Apply global alpha multiplier for transitions
    // Note: Actual alpha usage needs to be implemented within each draw function
    // This multiplier concept helps manage the transition fade.

    switch (mode) {
        case VIBE.CALM:
            drawCalmMode(alphaMultiplier);
            break;
        case VIBE.GROOVY:
            drawGroovyMode(alphaMultiplier);
            break;
        case VIBE.ENERGETIC:
            drawEnergeticMode(alphaMultiplier);
            break;
        case VIBE.INTENSE:
            drawIntenseMode(alphaMultiplier);
            break;
        default:
             drawCalmMode(alphaMultiplier); // Default to calm
            break;
    }
}


// =============================================================
// INDIVIDUAL MODE DRAWING FUNCTIONS (Implement Visual Logic Here!)
// =============================================================

function drawCalmMode(alphaMult) {
    // --- Visual Idea: Slow, flowing Perlin noise clouds/aurora ---
    calmCloudOffset += 0.001 + currentEnergy * 0.005; // Slow drift + energy influence
    let baseAlpha = 15 * alphaMult; // Base transparency

    push();
    for (let y = 0; y < height; y += 10) {
        beginShape();
        noFill();
        // Calculate hue based on centroid, saturation low for calm
        let hue = map(currentCentroid, 0, 1, 180, 270); // Blues to Purples
        let sat = 40 + currentBandwidth * 30; // Slightly more saturated if richer sound
        let brt = 60 + currentEnergy * 40; // Brighter if more energy
        stroke(hue, sat, brt, baseAlpha + currentEnergy * 20 * alphaMult); // More opaque with energy
        strokeWeight(map(currentEnergy, 0, 1, 1, 4));

        for (let x = -50; x < width + 50; x += 20) {
            let noiseVal = noise(x * 0.005, y * 0.008, calmCloudOffset);
            let yOffset = map(noiseVal, 0, 1, -60, 60) * (1 + currentEnergy * 2); // More displacement with energy
            curveVertex(x, y + yOffset);
        }
        endShape();
    }
    pop();
}

function drawGroovyMode(alphaMult) {
    // --- Visual Idea: Oscillating waves, orbiting particles ---
    push();
    translate(width / 2, height / 2); // Center effects

    let numWaves = 5 + Math.floor(currentBandwidth * 10);
    let maxRadius = min(width, height) * 0.4 * (0.8 + currentEnergy * 0.4); // Size pulsates slightly

    for (let i = 0; i < numWaves; i++) {
        beginShape();
        let hue = (currentHue + i * (360 / numWaves)) % 360;
        let sat = 80 + currentEnergy * 20;
        let brt = 100;
        strokeWeight(map(currentEnergy, 0, 1, 1, 3));
        stroke(hue, sat, brt, 70 * alphaMult);
        noFill();

        let timeOffset = millis() * 0.0005 * (currentBPM / 120); // Time based on BPM
        let complexity = 2 + Math.floor(currentBandwidth * 5); // More points if complex sound

        for (let angle = 0; angle < TWO_PI; angle += PI / 60) {
            // Combine sine waves for complexity
            let offset = 0;
            for(let j = 1; j <= complexity; j++){
                offset += sin(angle * (j*2) + timeOffset * j) * (maxRadius / (15 * j));
            }
             let r = maxRadius + offset * (0.5 + currentEnergy); // More amplitude with energy
            let x = cos(angle) * r;
            let y = sin(angle) * r;
            vertex(x, y);
        }
        endShape(CLOSE);
    }
    pop();

    // Add maybe some simple orbiting particles here too if desired
}

function drawEnergeticMode(alphaMult) {
    // --- Visual Idea: Radiating lines/shapes from center, beat pulses ---
     push();
     translate(width/2, height/2);

    // Background pulse based on energy
    let bgPulseSize = map(currentEnergy, 0.5, 1, 0, max(width, height) * 1.5, true); // Only pulse on high energy
    if (bgPulseSize > 0) {
        noStroke();
        fill(currentHue, 80, 100, 15 * alphaMult * (currentEnergy - 0.5)); // Fade in pulse
        ellipse(0, 0, bgPulseSize, bgPulseSize);
    }

     // Radiating lines
     let numLines = 20 + Math.floor(currentBandwidth * 40);
     let lineLength = min(width, height) * 0.6 * (0.5 + currentEnergy);
     strokeWeight(map(currentEnergy, 0, 1, 1, 4));

     for (let i = 0; i < numLines; i++){
         let angle = map(i, 0, numLines, 0, TWO_PI) + millis()*0.0001; // Slow rotation
         let hue = (currentHue + map(sin(angle*5 + millis()*0.001), -1, 1, -30, 30)) % 360; // Shifting hues
         let sat = 90;
         let brt = 100;
         let alpha = 40 + currentEnergy * 60; // Brighter lines with energy
         stroke(hue, sat, brt, alpha * alphaMult);

         let x = cos(angle) * lineLength;
         let y = sin(angle) * lineLength;
         line(0, 0, x, y);
     }

     // Simple beat flash (using energy peaks as proxy)
     if(currentEnergy > 0.7 && millis() - lastEnergyPeakTime > 100 * (180/currentBPM) ){ // Threshold + cooldown based on BPM
          fill(currentHue, 30, 100, 80 * alphaMult); // White-ish flash
          rect(-width/2, -height/2, width, height);
          lastEnergyPeakTime = millis();
     }

     pop();
}

function drawIntenseMode(alphaMult) {
    // --- Visual Idea: High particle count chaos, glitch effects, sharp changes ---
    let targetParticleCount = map(currentEnergy + currentBandwidth, 0, 2, 100, MAX_PARTICLES);
    manageParticles(targetParticleCount); // Add/remove particles

    glitchAmount = lerp(glitchAmount, currentEnergy * currentBandwidth, 0.1); // More glitch if high energy AND complex

    push();
    // Particle drawing (reuse basic particle, but make behaviour intense)
    for (let p of particles) {
        // Intense modifications
        p.maxSpeed = 5 + currentEnergy * 10; // Very fast
        p.noiseScl = 0.05 + currentBandwidth * 0.1; // High freq noise
        p.noiseTimeFactor = 0.05 + currentEnergy * 0.1;
        p.strokeW = 1 + currentEnergy * 3;

        // Color shifts rapidly based on centroid/bandwidth
        let hue = (currentHue + random(-60, 60) * currentBandwidth) % 360;
        let sat = 80 + random(0, 20);
        let bright = 100;
        let alpha = 50 + currentEnergy * 50;

        p.col = [hue, sat, bright, alpha * alphaMult]; // Assign color directly
        p.update();
        p.display();
        p.checkEdges();
    }
    pop();

    // Simple Glitch Effect (screen shake / color channel offset)
    if (random(1) < glitchAmount * 0.5) {
         loadPixels();
         let d = pixelDensity();
         let offset = floor(random(-10, 10) * glitchAmount);
         for (let y = 0; y < height; y++) {
             for (let x = 0; x < width; x++) {
                  if (random(1) < 0.8) continue; // Don't glitch every pixel

                 let i = 4 * d * (y * d * width + x); // Index in pixel array
                 let r_idx = i + 0;
                 let g_idx = i + 1;
                 let b_idx = i + 2;

                 let r_src_idx = 4 * d * (y * d * width + min(width*d -1, max(0, x + offset)));
                 let b_src_idx = 4 * d * (y * d * width + min(width*d -1, max(0, x - offset)));

                 pixels[r_idx] = pixels[r_src_idx + 0]; // Shift red channel
                 pixels[b_idx] = pixels[b_src_idx + 2]; // Shift blue channel oppositely
             }
         }
         updatePixels();
     }
}

// =============================================================
// VIBE DETERMINATION & TRANSITION
// =============================================================
function determineCurrentVibe(forceCalm = false) {
    let newVibe = VIBE.UNKNOWN;

    if(forceCalm) {
        newVibe = VIBE.CALM;
    } else {
        // Simple threshold-based classification (TUNE THESE VALUES!)
        let energyLevel = currentEnergy;
        let complexity = (currentCentroid + currentBandwidth) / 2; // Combine brightness/richness
        let bpmFactor = map(currentBPM, 60, 180, 0, 1, true); // Normalize BPM influence

        if (energyLevel < 0.25 && complexity < 0.4) {
            newVibe = VIBE.CALM;
        } else if (energyLevel < 0.5 && energyLevel > 0.2 && bpmFactor > 0.3 && bpmFactor < 0.7) {
            newVibe = VIBE.GROOVY;
        } else if (energyLevel > 0.6 && complexity > 0.6) {
             newVibe = VIBE.INTENSE;
        } else if (energyLevel > 0.5 || bpmFactor > 0.7) {
             newVibe = VIBE.ENERGETIC;
        } else if (energyLevel > 0.3) { // Fallback groovy/energetic border
            newVibe = VIBE.GROOVY;
        }
        else {
             newVibe = VIBE.CALM; // Default fallback
        }
    }


    // Start transition if vibe changes
    if (newVibe !== currentVisualMode && !transitioning) {
        console.log(`Vibe Change: ${currentVisualMode} -> ${newVibe}`);
        oldVisualMode = currentVisualMode;
        currentVisualMode = newVibe;
        transitioning = true;
        transitionProgress = 0;
        // Optional: Initialize elements for the *new* mode here
        initializeMode(currentVisualMode);
    }
}

function handleTransition() {
    if (transitioning) {
        transitionProgress += 0.03; // Speed of transition fade
        if (transitionProgress >= 1.0) {
            transitionProgress = 1.0;
            transitioning = false;
            oldVisualMode = currentVisualMode; // Update old mode once transition is complete
             console.log(`Transition Complete: Now in ${currentVisualMode}`);
             // Optional: Clean up elements from the *old* mode here
        }
    }
}

// Function to set up specifics for a mode (e.g., particle count)
function initializeMode(mode) {
     console.log("Initializing mode:", mode);
     // Example: Reset particle count based on mode starting point
     let targetCount = 0;
      switch (mode) {
        case VIBE.CALM: targetCount = 50; break;
        case VIBE.GROOVY: targetCount = 150; break;
        case VIBE.ENERGETIC: targetCount = 250; break;
        case VIBE.INTENSE: targetCount = 400; break;
        default: targetCount = 100; break;
    }
    //manageParticles(targetCount); // Adjust particle count immediately
     // Could also initialize groovyOrbits array, reset pulse timers etc.
     lastEnergyPeakTime = 0; // Reset peak timer
     glitchAmount = 0;
}

// Function to add/remove particles smoothly towards a target count
function manageParticles(targetCount) {
    targetCount = constrain(targetCount, 0, MAX_PARTICLES);
    let difference = targetCount - particles.length;

    if (difference > 0) {
        // Add particles (up to a few per frame)
        for (let i = 0; i < min(difference, 5); i++) {
            if (particles.length < MAX_PARTICLES) {
                 particles.push(new Particle(random(width), random(height)));
            }
        }
    } else if (difference < 0) {
        // Remove particles (up to a few per frame)
        for (let i = 0; i < min(-difference, 5); i++) {
            if (particles.length > 0) {
                particles.pop(); // Remove from the end
            }
        }
    }
}


// =============================================================
// MUSIC ANALYSIS UPDATE
// =============================================================
function updateMusicAnalysis() {
    if (!musicData || !audioPlayer || audioPlayer.paused || audioPlayer.ended) {
        // If music stops, maybe force fade to CALM? Handled in draw() now
        return;
    }
     if (currentDataIndex >= musicData.timeline.length){
         return;
     }

    let currentAudioTime = audioPlayer.currentTime;
    // Find the corresponding index in the analysis timeline
    while (currentDataIndex < musicData.timeline.length - 1 && musicData.timeline[currentDataIndex + 1] <= currentAudioTime) {
        currentDataIndex++;
    }
     if (currentDataIndex >= musicData.timeline.length) {
        currentDataIndex = musicData.timeline.length - 1;
     }

    // --- Update global parameters ---
    // Smooth values using lerp for less jittery visuals
    let smoothFactor = 0.1; // Adjust for more/less smoothing
    currentEnergy = lerp(currentEnergy, musicData.rms_energy[currentDataIndex], smoothFactor);
    currentCentroid = lerp(currentCentroid, musicData.spectral_centroid[currentDataIndex], smoothFactor);
    currentBandwidth = lerp(currentBandwidth, musicData.spectral_bandwidth[currentDataIndex], smoothFactor);
    currentBPM = musicData.overall_bpm; // BPM is usually constant for the track

    // Calculate base color properties (can be overridden by modes)
    currentHue = map(currentCentroid, 0, 1, 150, 360); // Blue -> Red range based on brightness
    currentSaturation = map(currentBandwidth, 0, 1, 70, 100); // More saturation if richer
    // currentBrightness is usually kept high for base elements

    // --- Check if Vibe Needs Updating ---
    if (millis() - lastVibeCheckTime > VIBE_CHECK_INTERVAL) {
        determineCurrentVibe();
        lastVibeCheckTime = millis();
    }
}


// =============================================================
// PARTICLE CLASS (Enhanced)
// =============================================================
class Particle {
    constructor(x, y) {
        this.pos = createVector(x, y);
        this.vel = createVector(random(-1, 1), random(-1, 1)); // Start with slight random velocity
        this.acc = createVector(0, 0);
        // Mode-dependent parameters (defaults set here, updated by modes)
        this.maxSpeed = 2;
        this.noiseScl = 0.01;
        this.noiseTimeFactor = 0.01;
        this.strokeW = 1.5;
        this.col = [180, 80, 100, 80]; // Default color (HSBA)
    }

    update() {
        // Use noiseTime for 3D noise, making the field evolve
        let noiseValueTime = noiseTime * this.noiseTimeFactor; // Mode can change evolution speed
        let angle = noise(this.pos.x * this.noiseScl, this.pos.y * this.noiseScl, noiseValueTime) * TWO_PI * 4;
        let force = p5.Vector.fromAngle(angle);
        force.setMag(0.1); // Base force magnitude
        this.acc.add(force);

        // Add slight attraction/repulsion from center based on energy? (Optional complexity)
        // let centerForce = p5.Vector.sub(createVector(width/2, height/2), this.pos);
        // centerForce.setMag( (currentEnergy - 0.5) * 0.01 ); // Attract if high energy, repel if low?
        // this.acc.add(centerForce);

        this.vel.add(this.acc);
        this.vel.limit(this.maxSpeed); // Use dynamic max speed
        this.pos.add(this.vel);
        this.acc.mult(0); // Reset acceleration
    }

    display() {
        stroke(this.col[0], this.col[1], this.col[2], this.col[3]); // Use assigned HSBA color
        strokeWeight(this.strokeW); // Use dynamic stroke weight
        point(this.pos.x, this.pos.y);
    }

    checkEdges() { // Wraparound
        if (this.pos.x > width) this.pos.x = 0;
        if (this.pos.x < 0) this.pos.x = width;
        if (this.pos.y > height) this.pos.y = 0;
        if (this.pos.y < 0) this.pos.y = height;
    }
}


// =============================================================
// UI INTERACTION (XMLHttpRequest - Keep as is)
// =============================================================
function initializeUploadListener() {
    document.getElementById('uploadButton').addEventListener('click', () => {
        let fileInput = document.getElementById('audioFileInput');
        if (fileInput.files.length === 0) { /* ... */ return; }
        let file = fileInput.files[0];
        let formData = new FormData();
        formData.append('audioFile', file);

        // Reset state
        statusMsg.textContent = 'Preparing upload...';
        uploadProgress.style.display = 'block';
        uploadProgress.value = 0;
        audioPlayer.style.display = 'none';
        audioPlayer.pause();
        audioPlayer.removeAttribute('src');
        musicData = null;
        currentDataIndex = 0;
        transitioning = false; // Ensure not stuck in transition
        currentVisualMode = VIBE.CALM; // Reset to calm
        oldVisualMode = VIBE.CALM;
        initializeMode(currentVisualMode);


        let xhr = new XMLHttpRequest();
        xhr.open('POST', '/analyze', true);

        xhr.upload.onprogress = function (event) {
             if (event.lengthComputable) {
                let percentComplete = (event.loaded / event.total) * 100;
                uploadProgress.value = percentComplete;
                statusMsg.textContent = `Uploading: ${Math.round(percentComplete)}%`;
            }
        };
        xhr.onload = function () {
            uploadProgress.style.display = 'none';
            if (xhr.status === 200) {
                statusMsg.textContent = 'Analysis complete! Starting...'; // Changed message
                try {
                    let data = JSON.parse(xhr.responseText);
                     if (data.error) {
                         statusMsg.textContent = `Analysis Error: ${data.error}`; console.error('Analysis Error:', data.error); musicData = null;
                     } else {
                        console.log('Analysis Received:', data);
                        musicData = data;
                        let objectURL = URL.createObjectURL(file);
                        audioPlayer.src = objectURL;
                        audioPlayer.oncanplaythrough = () => {
                            currentDataIndex = 0;
                            audioPlayer.play();
                            statusMsg.textContent = 'Visualizing...'; // Changed message
                            lastVibeCheckTime = millis(); // Reset vibe check timer
                        };
                        audioPlayer.onended = () => {
                            statusMsg.textContent = 'Playback finished.'; musicData = null;
                            // Optional: fade out visuals or transition to default state
                        };
                    }
                } catch (e) {
                     statusMsg.textContent = 'Error processing analysis.'; console.error('Processing Error:', e); musicData = null;
                }
            } else {
                statusMsg.textContent = `Error: Upload/Analysis Failed (Status: ${xhr.status})`; console.error('Upload/Analysis Error:', xhr.statusText); musicData = null;
            }
        };
        xhr.onerror = function () {
            uploadProgress.style.display = 'none'; statusMsg.textContent = 'Network Error.'; console.error('Network Error'); musicData = null;
        };
        statusMsg.textContent = 'Uploading (0%)...';
        xhr.send(formData);
    });
} // End of initializeUploadListener