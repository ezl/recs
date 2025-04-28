/**
 * Add Recommendation Page
 * Handles text and audio input modes for adding recommendations
 */

document.addEventListener('DOMContentLoaded', function() {
    // Auto focus the textarea if it exists
    const textRecommendations = document.getElementById('text-recommendations');
    if (textRecommendations) {
        textRecommendations.focus();
    }
    
    // Form elements
    const form = document.getElementById('step1-form');
    const submitButton = document.getElementById('submit-button');
    const buttonText = submitButton ? submitButton.querySelector('span') : null;
    const arrowIcon = submitButton ? submitButton.querySelector('svg:not(#spinner)') : null;
    const spinner = document.getElementById('spinner');
    const footer = document.getElementById('footer');
    
    // Log UI elements status for debugging
    console.log("UI Elements Status:");
    console.log("- form:", form ? "found" : "missing");
    console.log("- submitButton:", submitButton ? "found" : "missing");
    console.log("- buttonText:", buttonText ? "found" : "missing");
    console.log("- arrowIcon:", arrowIcon ? "found" : "missing");
    console.log("- spinner:", spinner ? "found" : "missing");
    console.log("- footer:", footer ? "found" : "missing");
    
    // Input toggle
    const toggleBtn = document.getElementById('toggle-input-btn');
    const textModeLabel = document.getElementById('text-mode-label');
    const audioModeLabel = document.getElementById('audio-mode-label');
    const textInputContainer = document.getElementById('text-input-container');
    const audioInputContainer = document.getElementById('audio-input-container');
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
    let errorTimeout;
    
    // Add manual validation for the textarea
    if (textRecommendations && submitButton) {
        // Initial validation
        validateTextInput();
        
        // Add event listener for input
        textRecommendations.addEventListener('input', validateTextInput);
        
        function validateTextInput() {
            const minLength = 10;
            const textLength = textRecommendations.value.trim().length;
            console.log('Text length:', textLength, 'Required:', minLength);
            
            if (textLength >= minLength) {
                submitButton.disabled = false;
                submitButton.classList.remove('btn-disabled');
                console.log('Submit button enabled');
            } else {
                submitButton.disabled = true;
                submitButton.classList.add('btn-disabled');
                console.log('Submit button disabled');
            }
        }
    }
    
    // Add navigation error handling for debugging
    window.addEventListener('error', function(event) {
        console.error('Navigation error:', event);
        if (event.target && (event.target.tagName === 'LINK' || event.target.tagName === 'SCRIPT')) {
            console.error('Resource failed to load:', event.target.src || event.target.href);
        }
    });
    
    // Show error function using server-side flash message
    function showError(message) {
        // Get trip slug from data attribute
        const tripSlug = document.getElementById('trip-data')?.dataset.slug;
        
        console.error('ERROR MESSAGE:', message);
        console.error('------------ STOPPING EXECUTION - DEBUG MODE ------------');
        
        // TEMPORARILY DISABLE RELOAD FOR DEBUGGING
        console.warn('Page reload disabled for debugging. Error would normally show:', message);
        
        // Create an error box on the page instead of reloading
        const errorBox = document.createElement('div');
        errorBox.style.position = 'fixed';
        errorBox.style.top = '20px';
        errorBox.style.left = '20px';
        errorBox.style.right = '20px';
        errorBox.style.backgroundColor = '#ffe0e0';
        errorBox.style.color = '#d00';
        errorBox.style.padding = '15px';
        errorBox.style.borderRadius = '5px';
        errorBox.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';
        errorBox.style.zIndex = '9999';
        errorBox.innerHTML = `
            <h3 style="margin-top:0;">Error Detected - Debug Mode</h3>
            <p>${message}</p>
            <p style="font-size:0.9em;">Page reload prevented for debugging. Check console for full logs.</p>
        `;
        document.body.appendChild(errorBox);
        
        // COMMENTED OUT FOR DEBUGGING
        /*
        // Call server-side endpoint to show flash message
        fetch(`/trip/${encodeURIComponent(tripSlug)}/audio-error?message=${encodeURIComponent(message)}`)
            .then(() => {
                // Reload the page to show the flash message
                console.log('Reloading page to show error message');
                window.location.reload();
            })
            .catch(error => {
                console.error('Error showing flash message:', error);
                // Fallback to alert if fetch fails
                alert(message);
            });
        */
    }

    // Form submission for text input
    function submitForm() {
        console.log('submitForm called');
        // Validate the form
        if (!form.checkValidity()) {
            console.log('Form validation failed');
            return false; // Prevent submission if invalid
        }

        console.log('Form validation passed, proceeding with submission');
        
        // Log the form data before submission
        const formData = new FormData(form);
        console.log('Form data to be submitted:', {
            unstructured_recommendations: formData.get('unstructured_recommendations'),
            audio_recommendations: formData.get('audio_recommendations')
        });
        
        // Show loading overlay
        if (typeof showLoadingOverlay === 'function') {
            console.log('Calling showLoadingOverlay directly');
            showLoadingOverlay(
                form.dataset.loadingTitle || "Processing your recommendations...",
                form.dataset.loadingSubtitle || "We're identifying the places you've recommended"
            );
        } else {
            console.error('showLoadingOverlay function not found!');
        }

        // Update UI to show submission is in progress
        submitButton.disabled = true;
        submitButton.classList.add('btn-disabled');
        arrowIcon.classList.add('hidden');
        spinner.classList.remove('hidden');
        buttonText.textContent = 'Processing...';

        // Submit the form programmatically
        console.log('Submitting form...');
        form.submit();

        // Prevent the default form submission since we're handling it manually
        return false;
    }

    // Keyboard shortcut handler
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && (e.altKey || e.metaKey) && !submitButton.disabled) {
            console.log('Cmd+Enter pressed, calling submitForm()');
            // Don't prevent default, let the form submit naturally
            submitForm();
        }
    });

    // Form submit button click handler
    submitButton.addEventListener('click', function(e) {
        // Don't prevent default, let the form submit naturally
        submitForm();
    });

    // Toggle between text and audio modes
    toggleBtn.addEventListener('click', function() {
        audioMode = !audioMode;
        
        if (audioMode) {
            // Switch to audio mode
            textInputContainer.classList.add('hidden');
            audioInputContainer.style.display = 'flex';
            audioInputContainer.classList.add('show-audio');
            textModeLabel.classList.remove('hidden');
            audioModeLabel.classList.add('hidden');
            footer.classList.add('hidden');
            
            // Reset audio UI
            recordingStatus.classList.add('hidden');
            recordBtn.classList.remove('recording');
            micWaves.classList.add('hidden');
            audioPlayerContainer.classList.add('hidden');
            
            // Automatically start recording
            setTimeout(() => {
                startRecording();
            }, 300);
        } else {
            // Switch to text mode
            textInputContainer.classList.remove('hidden');
            audioInputContainer.style.display = 'none';
            audioInputContainer.classList.remove('show-audio');
            textModeLabel.classList.add('hidden');
            audioModeLabel.classList.remove('hidden');
            footer.classList.remove('hidden');
            
            // Stop recording if active
            if (recording) {
                stopRecording();
            }
            
            // Focus the text input
            setTimeout(() => {
                textRecommendations.focus();
            }, 100);
        }
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
            console.log("Requesting microphone access...");
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            console.log("Microphone access granted");
            
            // Ensure audio player is hidden when starting a new recording
            audioPlayerContainer.classList.add('hidden');
            
            // Log the audio tracks and their settings
            const audioTracks = stream.getAudioTracks();
            console.log(`Got ${audioTracks.length} audio tracks`);
            audioTracks.forEach((track, index) => {
                console.log(`Track ${index} settings:`, track.getSettings());
            });
            
            // Check supported MIME types
            const supportedMimeTypes = [
                'audio/webm',
                'audio/webm;codecs=opus',
                'audio/mp4',
                'audio/mp4;codecs=mp4a',
                'audio/ogg',
                'audio/ogg;codecs=opus'
            ];
            
            // Find a supported MIME type
            let mimeType = null;
            for (const type of supportedMimeTypes) {
                if (MediaRecorder.isTypeSupported(type)) {
                    mimeType = type;
                    console.log(`Using supported MIME type: ${mimeType}`);
                    break;
                }
            }
            
            // Create MediaRecorder with proper options
            const options = {};
            if (mimeType) {
                options.mimeType = mimeType;
            }
            
            mediaRecorder = new MediaRecorder(stream, options);
            
            console.log("MediaRecorder created with settings:", mediaRecorder);
            console.log("MediaRecorder mime type:", mediaRecorder.mimeType);
            
            // Start recording
            audioChunks = [];
            mediaRecorder.start();
            recording = true;
            
            console.log("Recording started");
            
            // Update UI
            recordBtn.classList.add('recording');
            micWaves.classList.remove('hidden');
            recordingStatus.classList.remove('hidden');
            recordingStatus.textContent = 'Recording... Press button to finish.';
            
            // Start timer
            startTimer();
            
            // Handle data
            mediaRecorder.addEventListener('dataavailable', function(e) {
                console.log(`Data chunk received, size: ${e.data.size} bytes`);
                audioChunks.push(e.data);
            });
            
            mediaRecorder.addEventListener('stop', function() {
                console.log(`Recording stopped, total chunks: ${audioChunks.length}`);
                
                // Create audio blob
                blob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
                console.log(`Blob created, size: ${blob.size} bytes, type: ${blob.type}`);
                
                // Create URL for playback (but don't show the player)
                const audioURL = URL.createObjectURL(blob);
                audioPlayback.src = audioURL;
                
                // Keep audio player hidden
                audioPlayerContainer.classList.add('hidden');
                
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
            
            // Ensure audio player remains hidden
            audioPlayerContainer.classList.add('hidden');
            
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
                console.log("Reached maximum recording time of 5 minutes");
                stopRecording();
            }
        }, 1000);
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
        console.log("========== AUDIO FLOW START ==========");
        console.log("Starting audio transcription process");
        console.log(`Audio blob size: ${audioBlob.size} bytes, type: ${audioBlob.type}`);
        
        // Ensure the audio player container remains hidden
        audioPlayerContainer.classList.add('hidden');
        
        // Check if the blob is valid
        if (audioBlob.size === 0) {
            console.error("Audio blob is empty (0 bytes)");
            showError("Recording failed. Please try again or use text input instead.");
            return;
        }
        
        // Create a FormData object to send the file
        const formData = new FormData();
        
        // Append blob with the proper filename and content type
        const extension = audioBlob.type.includes('mp4') ? 'mp4' : 'webm';
        formData.append('audio', audioBlob, `recording.${extension}`);
        formData.append('destination', document.getElementById('destination-data').dataset.destination);
        
        console.log(`FormData created with audio file named recording.${extension}`);
        console.log(`Destination: ${document.getElementById('destination-data').dataset.destination}`);
        console.log("Preparing to send audio to server...");
        
        try {
            console.log("SENDING: Audio data to /api/transcribe endpoint");
            const startTime = new Date();
            console.log(`Request start time: ${startTime.toISOString()}`);
            
            // Use fetch to send the audio file to the server for transcription
            const response = await fetch('/api/transcribe', {
                method: 'POST',
                body: formData
            });
            
            const endTime = new Date();
            const duration = (endTime - startTime) / 1000;
            console.log(`RECEIVED: Server response after ${duration} seconds`);
            console.log(`Response status: ${response.status}, statusText: ${response.statusText}`);
            console.log(`Response headers:`, response.headers);
            
            if (!response.ok && response.status !== 200) {
                const errorText = await response.text();
                console.error(`Server error response: ${response.status}`, errorText);
                throw new Error(`Failed to transcribe audio: ${response.status} ${errorText}`);
            }
            
            console.log("PARSING: JSON response from server");
            const data = await response.json();
            console.log("RECEIVED DATA:", data);
            console.log("Data structure:", JSON.stringify(data, null, 2));
            
            // Check if we received a transcription even if recommendations failed
            if (data.transcription) {
                console.log("Transcription received, first 100 chars:", data.transcription.substring(0, 100));
                console.log("Transcription length:", data.transcription.length);
            } else {
                console.warn("No transcription in response");
            }
            
            // Check for recommendations
            if (data.recommendations) {
                console.log(`Recommendations received: ${data.recommendations.length} items`);
                data.recommendations.forEach((rec, i) => {
                    console.log(`Recommendation ${i+1}: ${rec.name} (${rec.type || 'No type'})`);
                });
            } else {
                console.warn("No recommendations in response");
            }
            
            // Check for partial success (transcription succeeded but recommendations failed)
            if (data.status === "partial_success") {
                console.warn("Partial success - got transcription but recommendation extraction failed:", data.error);
                
                // Create an emergency fallback with just the transcription
                const fallbackRecommendation = [{
                    name: "Recommendations from recording",
                    type: "",
                    website_url: "",
                    description: data.transcription
                }];
                
                console.log("Created fallback recommendation with transcription text");
                
                // Store the fallback recommendation
                audioRecommendations.value = JSON.stringify(fallbackRecommendation);
                console.log("Set audioRecommendations.value to:", audioRecommendations.value);
                
                // Allow form submission
                submitButton.disabled = false;
                submitButton.classList.remove('btn-disabled');
                console.log("Submit button enabled for partial success");
                
                // Automatically submit the form
                console.log("CALLING: submitForm() with partial success data");
                submitForm();
                return;
            }
            
            // Store the transcribed text in a hidden field to be submitted with the form
            if (data.recommendations && data.recommendations.length > 0) {
                console.log(`PROCESSING: ${data.recommendations.length} recommendations for form submission`);
                
                // Store the recommendations in the hidden input
                audioRecommendations.value = JSON.stringify(data.recommendations);
                console.log("Set audioRecommendations.value to JSON string of length:", audioRecommendations.value.length);
                
                // Allow form submission
                submitButton.disabled = false;
                submitButton.classList.remove('btn-disabled');
                console.log("Submit button enabled for recommendations");
                
                // Automatically submit the form
                console.log("CALLING: submitForm() with recommendations data");
                submitForm();
            } else {
                console.error("No recommendations found in response:", data);
                
                // If we have a transcription but no recommendations, create a fallback
                if (data.transcription) {
                    console.log("Creating fallback from transcription since no recommendations were extracted");
                    const fallbackRecommendation = [{
                        name: "Recommendations from recording",
                        type: "",
                        website_url: "",
                        description: data.transcription
                    }];
                    
                    // Store the fallback recommendation
                    audioRecommendations.value = JSON.stringify(fallbackRecommendation);
                    console.log("Set audioRecommendations.value with fallback:", audioRecommendations.value);
                    
                    // Allow form submission
                    submitButton.disabled = false;
                    submitButton.classList.remove('btn-disabled');
                    console.log("Submit button enabled for fallback");
                    
                    // Automatically submit the form
                    console.log("CALLING: submitForm() with fallback recommendation");
                    submitForm();
                } else {
                    throw new Error("Server returned success but no recommendations or transcription were found");
                }
            }
        } catch (error) {
            console.error('Error processing audio:', error);
            console.error('Error stack:', error.stack);
            showError('There was an error processing your audio. Please try again or use text input instead.');
            
            // Ensure audio player remains hidden
            audioPlayerContainer.classList.add('hidden');
            
            // Switch back to text mode
            audioMode = true; // Needs to be true before toggle changes it
            toggleBtn.click();
        } finally {
            // Hide transcription status
            transcriptionStatus.classList.add('hidden');
            console.log("Transcription process completed");
        }
    }
}); 