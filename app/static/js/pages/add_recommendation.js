/**
 * Add Recommendation Page
 * Handles text and audio input modes for adding recommendations
 */

document.addEventListener('DOMContentLoaded', function() {
    // Auto focus the textarea
    document.getElementById('text-recommendations').focus();
    
    // Form elements
    const form = document.getElementById('step1-form');
    const submitButton = document.getElementById('submit-button');
    const buttonText = submitButton.querySelector('span');
    const arrowIcon = submitButton.querySelector('svg:not(#spinner)');
    const spinner = document.getElementById('spinner');
    const footer = document.getElementById('footer');
    const errorToast = document.getElementById('error-toast');
    const errorMessage = document.getElementById('error-message');
    
    // Input toggle
    const toggleBtn = document.getElementById('toggle-input-btn');
    const textModeLabel = document.getElementById('text-mode-label');
    const audioModeLabel = document.getElementById('audio-mode-label');
    const textInputContainer = document.getElementById('text-input-container');
    const audioInputContainer = document.getElementById('audio-input-container');
    const textRecommendations = document.getElementById('text-recommendations');
    const audioRecommendations = document.getElementById('audio-recommendations');
    
    // Audio recording elements
    const recordBtn = document.getElementById('record-btn');
    const micWaves = document.querySelector('.mic-waves');
    const recordingStatus = document.getElementById('recording-status');
    const recordingTime = document.getElementById('recording-time');
    const minutesDisplay = document.getElementById('minutes');
    const secondsDisplay = document.getElementById('seconds');
    const audioPlayerContainer = document.getElementById('audio-player-container');
    const audioPlayback = document.getElementById('audio-playback');
    const transcriptionStatus = document.getElementById('transcription-status');
    
    // Variables for recording
    let mediaRecorder;
    let audioChunks = [];
    let recording = false;
    let timer;
    let seconds = 0;
    let blob;
    let audioMode = false;
    let recognitionTimeout;
    let errorTimeout;

    // Show error toast
    function showError(message) {
        // Clear any existing timeout
        if (errorTimeout) {
            clearTimeout(errorTimeout);
            errorToast.classList.add('hidden');
        }
        
        // Update error message
        errorMessage.textContent = message;
        
        // Show the toast
        errorToast.classList.remove('hidden');
        
        // Force a reflow to restart the animation
        errorToast.offsetHeight;
        
        // Set timeout to hide the toast after animation completes
        errorTimeout = setTimeout(() => {
            errorToast.classList.add('hidden');
        }, 6000); // Animation duration + display time
    }

    // Enable/disable submit button based on input
    function updateSubmitButton() {
        if (audioMode) {
            // In audio mode, enable if audio is recorded
            submitButton.disabled = !audioPlayback.src;
        } else {
            // In text mode, enable if text is entered
            submitButton.disabled = !textRecommendations.value.trim();
        }
    }
    
    // Initialize to disabled
    submitButton.disabled = true;
    
    // Listen for text input
    textRecommendations.addEventListener('input', updateSubmitButton);
    
    // Add Alt+Enter keyboard shortcut to submit form
    textRecommendations.addEventListener('keydown', function(e) {
        // Check if Alt+Enter was pressed
        if (e.key === 'Enter' && e.altKey && !submitButton.disabled) {
            e.preventDefault(); // Prevent default behavior (newline)
            form.submit(); // Submit the form
            
            // Update UI to show submission is in progress
            submitButton.disabled = true;
            submitButton.classList.add('opacity-75', 'cursor-not-allowed');
            arrowIcon.classList.add('hidden');
            spinner.classList.remove('hidden');
            buttonText.textContent = 'Processing...';
        }
    });
    
    // Toggle between text and audio modes
    toggleBtn.addEventListener('click', function() {
        audioMode = !audioMode;
        
        if (audioMode) {
            textInputContainer.classList.add('hidden');
            audioInputContainer.classList.remove('hidden');
            textModeLabel.classList.remove('hidden');
            audioModeLabel.classList.add('hidden');
            footer.classList.add('hidden');
            
            // Automatically start recording
            startRecording();
        } else {
            textInputContainer.classList.remove('hidden');
            audioInputContainer.classList.add('hidden');
            textModeLabel.classList.add('hidden');
            audioModeLabel.classList.remove('hidden');
            footer.classList.remove('hidden');
            
            // Stop recording if active
            if (recording) {
                stopRecording();
            }
        }
        
        updateSubmitButton();
    });
    
    // Audio recording functionality
    recordBtn.addEventListener('click', toggleRecording);
    
    function toggleRecording() {
        if (!recording) {
            startRecording();
        } else {
            stopRecording();
        }
    }
    
    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            
            // Start recording
            audioChunks = [];
            mediaRecorder.start();
            recording = true;
            
            // Update UI
            recordBtn.classList.add('recording');
            micWaves.classList.remove('hidden');
            recordingStatus.textContent = 'Recording... Press button to finish.';
            
            // Hide player and reset if there was a previous recording
            audioPlayerContainer.classList.add('hidden');
            audioPlayback.src = '';
            
            // Start timer
            startTimer();
            
            // Handle data
            mediaRecorder.addEventListener('dataavailable', function(e) {
                audioChunks.push(e.data);
            });
            
            mediaRecorder.addEventListener('stop', function() {
                // Create audio blob
                blob = new Blob(audioChunks, { type: 'audio/webm' });
                
                // Create URL for playback (still needed for submission but not shown)
                const audioURL = URL.createObjectURL(blob);
                audioPlayback.src = audioURL;
                
                // Process for transcription
                processAudioForTranscription(blob);
            });
        } catch (err) {
            console.error('Error accessing microphone:', err);
            showError('Unable to access your microphone. Please ensure it is connected and you have granted permission.');
        }
    }
    
    function stopRecording() {
        if (mediaRecorder && recording) {
            mediaRecorder.stop();
            recording = false;
            
            // Update UI
            recordBtn.classList.remove('recording');
            micWaves.classList.add('hidden');
            recordingStatus.textContent = 'Processing...';
            
            // Stop timer
            clearInterval(timer);
        }
    }
    
    function startTimer() {
        seconds = 0;
        updateTimerDisplay();
        
        timer = setInterval(function() {
            seconds++;
            updateTimerDisplay();
            
            // Auto-stop after 5 minutes (300 seconds)
            if (seconds >= 300) {
                stopRecording();
            }
            
            // Auto-stop after 3 seconds of silence (simplified version)
            if (seconds >= 5 && seconds % 5 === 0) {
                // This is a simplified check that would be replaced by actual silence detection
                // For now, we'll use a crude timeout-based approach
                checkSilence();
            }
        }, 1000);
    }
    
    // Simple function to check for silence - in a real app, this would analyze audio levels
    function checkSilence() {
        // Clear any existing timeout
        if (recognitionTimeout) clearTimeout(recognitionTimeout);
        
        // Set a new timeout - if nothing happens in 3 seconds, stop recording
        recognitionTimeout = setTimeout(() => {
            if (recording && seconds > 10) { // Only auto-stop if we've recorded at least 10 seconds
                stopRecording();
            }
        }, 3000);
    }
    
    function updateTimerDisplay() {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        minutesDisplay.textContent = minutes.toString().padStart(2, '0');
        secondsDisplay.textContent = remainingSeconds.toString().padStart(2, '0');
    }
    
    async function processAudioForTranscription(audioBlob) {
        // Show transcription status
        transcriptionStatus.classList.remove('hidden');
        
        // Create a FormData object to send the file
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        formData.append('destination', document.getElementById('destination-data').dataset.destination);
        
        try {
            // Use fetch to send the audio file to the server for transcription
            const response = await fetch('/api/transcribe', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Failed to transcribe audio');
            }
            
            const data = await response.json();
            
            // Store the transcribed text in a hidden field to be submitted with the form
            if (data.recommendations) {
                // Store the recommendations in the hidden input
                audioRecommendations.value = JSON.stringify(data.recommendations);
                
                // Allow form submission
                submitButton.disabled = false;
                
                // Automatically submit the form
                submitForm();
            }
        } catch (error) {
            console.error('Error processing audio:', error);
            showError('There was an error processing your audio. Please try again or use text input instead.');
            
            // Switch back to text mode
            audioMode = true; // Needs to be true before toggle changes it
            toggleBtn.click();
        } finally {
            // Hide transcription status
            transcriptionStatus.classList.add('hidden');
        }
    }

    // Function to submit the form
    function submitForm() {
        // If in audio mode and we have processed audio data
        if (audioMode && audioRecommendations.value) {
            // Disable button
            submitButton.disabled = true;
            submitButton.classList.add('opacity-75', 'cursor-not-allowed');
            
            // Hide arrow icon, show spinner
            arrowIcon.classList.add('hidden');
            spinner.classList.remove('hidden');
            
            // Change text
            buttonText.textContent = 'Processing...';
            
            // Get trip slug from data attribute
            const tripSlug = document.getElementById('trip-data').dataset.slug;
            
            // Post the audio recommendations directly
            fetch(`/trip/${encodeURIComponent(tripSlug)}/process-audio`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: audioRecommendations.value
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Redirect to the confirmation page
                window.location.href = data.redirect_url;
            })
            .catch(error => {
                console.error('Error:', error);
                showError('There was an error processing your audio. Please try again.');
                
                // Re-enable button
                submitButton.disabled = false;
                submitButton.classList.remove('opacity-75', 'cursor-not-allowed');
                arrowIcon.classList.remove('hidden');
                spinner.classList.add('hidden');
                buttonText.textContent = 'Continue';
            });
        }
    }

    // Form submission for text input
    form.addEventListener('submit', function(e) {
        if (!form.checkValidity()) {
            return;
        }
        
        // For text mode, just disable the button and show spinner
        if (!audioMode) {
            submitButton.disabled = true;
            submitButton.classList.add('opacity-75', 'cursor-not-allowed');
            
            // Hide arrow icon, show spinner
            arrowIcon.classList.add('hidden');
            spinner.classList.remove('hidden');
            
            // Change text
            buttonText.textContent = 'Processing...';
        } else {
            // For audio mode, prevent default form submission as we handle it separately
            e.preventDefault();
        }
    });
}); 