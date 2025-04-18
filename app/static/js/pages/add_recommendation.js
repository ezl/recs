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
    
    // Add Alt+Enter or Command+Enter keyboard shortcut to submit form
    document.addEventListener('keydown', function(e) {
        // Check if Alt+Enter or Command+Enter was pressed
        if (e.key === 'Enter' && (e.altKey || e.metaKey) && !submitButton.disabled) {
            e.preventDefault(); // Prevent default behavior (newline)
            
            // If in text mode, submit form directly
            if (!audioMode) {
                form.submit(); // Submit the form
                
                // Update UI to show submission is in progress
                submitButton.disabled = true;
                submitButton.classList.add('opacity-75', 'cursor-not-allowed');
                arrowIcon.classList.add('hidden');
                spinner.classList.remove('hidden');
                buttonText.textContent = 'Processing...';
            } else if (audioRecommendations.value) {
                // In audio mode with processed audio, submit it
                submitForm();
            }
        }
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
            console.log("Requesting microphone access...");
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            console.log("Microphone access granted");
            
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
            
            // Hide player and reset if there was a previous recording
            audioPlayerContainer.classList.add('hidden');
            audioPlayback.src = '';
            
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
                
                // Create URL for playback
                const audioURL = URL.createObjectURL(blob);
                audioPlayback.src = audioURL;
                
                // Show audio player
                audioPlayerContainer.classList.remove('hidden');
                
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
            
            // Switch back to text mode
            audioMode = true; // Needs to be true before toggle changes it
            toggleBtn.click();
        } finally {
            // Hide transcription status
            transcriptionStatus.classList.add('hidden');
            console.log("Transcription process completed");
        }
    }

    // Function to submit the form
    function submitForm() {
        console.log("========== SUBMIT FORM START ==========");
        console.log("submitForm() called");
        
        // If in audio mode and we have processed audio data
        if (audioMode && audioRecommendations.value) {
            console.log("In audio mode with recommendation data, length:", audioRecommendations.value.length);
            console.log("First 100 chars of data:", audioRecommendations.value.substring(0, 100) + "...");
            
            try {
                // Parse to make sure it's valid JSON
                const recommendationsData = JSON.parse(audioRecommendations.value);
                console.log("Successfully parsed recommendations data:", recommendationsData);
                console.log(`Parsed ${recommendationsData.length} recommendations`);
                
                if (!Array.isArray(recommendationsData)) {
                    console.error("Recommendations data is not an array:", recommendationsData);
                    showError("There was an error with the recommendation format. Please try again.");
                    return;
                }
                
                if (recommendationsData.length === 0) {
                    console.error("Recommendations array is empty");
                    showError("No recommendations were found in your recording. Please try again with more specific details.");
                    return;
                }
            } catch (error) {
                console.error("Failed to parse recommendations data:", error);
                console.error("Raw value:", audioRecommendations.value);
                showError("There was an error processing your audio data. Please try again.");
                return;
            }
            
            // Disable button
            submitButton.disabled = true;
            submitButton.classList.add('opacity-75', 'cursor-not-allowed');
            console.log("UI: Submit button disabled for form submission");
            
            // Check if arrowIcon exists before trying to use it
            if (arrowIcon) {
                // Hide arrow icon, show spinner
                arrowIcon.classList.add('hidden');
                console.log("UI: Arrow icon hidden");
            } else {
                console.warn("UI: arrowIcon is null, skipping hide operation");
            }
            
            // Check if spinner exists before trying to use it
            if (spinner) {
                spinner.classList.remove('hidden');
                console.log("UI: Spinner shown");
            } else {
                console.warn("UI: spinner is null, skipping show operation");
            }
            
            // Change text
            if (buttonText) {
                buttonText.textContent = 'Processing...';
                console.log("UI: Button text updated to 'Processing...'");
            } else {
                console.warn("UI: buttonText is null, skipping text update");
            }
            
            // Get trip slug from data attribute
            const tripDataElement = document.getElementById('trip-data');
            if (!tripDataElement) {
                console.error("ERROR: trip-data element not found!");
                showError("There was an error identifying the trip. Please refresh the page and try again.");
                
                // Re-enable button
                submitButton.disabled = false;
                submitButton.classList.remove('opacity-75', 'cursor-not-allowed');
                
                // Check if arrowIcon exists before trying to use it
                if (arrowIcon) {
                    arrowIcon.classList.remove('hidden');
                } else {
                    console.warn("UI: arrowIcon is null, skipping show operation in error handler");
                }
                
                // Check if spinner exists before trying to use it
                if (spinner) {
                    spinner.classList.add('hidden');
                } else {
                    console.warn("UI: spinner is null, skipping hide operation in error handler");
                }
                
                // Change text back
                if (buttonText) {
                    buttonText.textContent = 'Continue';
                } else {
                    console.warn("UI: buttonText is null, skipping text update in error handler");
                }
                return;
            }
            
            const tripSlug = tripDataElement.dataset.slug;
            console.log("Trip slug for submission:", tripSlug);
            
            if (!tripSlug) {
                console.error("ERROR: trip slug not found in data attribute!");
                showError("There was an error identifying the trip. Please refresh the page and try again.");
                
                // Re-enable button
                submitButton.disabled = false;
                submitButton.classList.remove('opacity-75', 'cursor-not-allowed');
                
                // Check if arrowIcon exists before trying to use it
                if (arrowIcon) {
                    arrowIcon.classList.remove('hidden');
                } else {
                    console.warn("UI: arrowIcon is null, skipping show operation in error handler");
                }
                
                // Check if spinner exists before trying to use it
                if (spinner) {
                    spinner.classList.add('hidden');
                } else {
                    console.warn("UI: spinner is null, skipping hide operation in error handler");
                }
                
                // Change text back
                if (buttonText) {
                    buttonText.textContent = 'Continue';
                } else {
                    console.warn("UI: buttonText is null, skipping text update in error handler");
                }
                return;
            }
            
            // Post the audio recommendations directly
            const postUrl = `/trip/${encodeURIComponent(tripSlug)}/process-audio`;
            console.log("SENDING: POST request to", postUrl);
            console.log("Request body length:", audioRecommendations.value.length);
            
            const startTime = new Date();
            console.log(`Request start time: ${startTime.toISOString()}`);
            
            fetch(postUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: audioRecommendations.value
            })
            .then(response => {
                const endTime = new Date();
                const duration = (endTime - startTime) / 1000;
                console.log(`RECEIVED: Server response after ${duration} seconds`);
                console.log("Process audio response received:", response.status, response.statusText);
                console.log("Response headers:", response.headers);
                
                if (!response.ok) {
                    console.error("Response not OK:", response.status, response.statusText);
                    return response.text().then(text => {
                        console.error("Error response body:", text);
                        throw new Error(`Network response was not ok: ${response.status} ${response.statusText} - ${text}`);
                    });
                }
                console.log("PARSING: JSON response from process-audio endpoint");
                return response.json();
            })
            .then(data => {
                console.log("RECEIVED DATA from process-audio:", data);
                
                // Check if we have a redirect URL
                if (!data.redirect_url) {
                    console.error("No redirect_url in response:", data);
                    throw new Error("Server response missing redirect URL");
                }
                
                // Redirect to the confirmation page
                console.log("REDIRECTING to:", data.redirect_url);
                
                try {
                    // Use a more robust approach to redirection
                    const redirectURL = new URL(data.redirect_url, window.location.origin);
                    console.log("Full redirect URL:", redirectURL.href);
                    
                    // Try to navigate directly
                    console.log("NAVIGATION: Attempting window.location.href redirect");
                    window.location.href = redirectURL.href;
                    
                    // Set a timeout to check if navigation occurred
                    setTimeout(() => {
                        console.log("NAVIGATION CHECK: Still on page after 1000ms, trying alternative redirect");
                        
                        // Alternative redirect method
                        console.log("NAVIGATION: Attempting window.location.replace redirect");
                        window.location.replace(redirectURL.href);
                        
                        // Last resort - create and click a link
                        setTimeout(() => {
                            console.log("NAVIGATION CHECK: Still on page after 2000ms, creating fallback link");
                            console.log("NAVIGATION: Final redirect attempt with link click");
                            const link = document.createElement('a');
                            link.href = redirectURL.href;
                            link.textContent = "Continue to recommendations";
                            link.style.display = "inline-block";
                            link.style.margin = "20px auto";
                            link.style.padding = "10px 20px";
                            link.style.backgroundColor = "#3b82f6";
                            link.style.color = "white";
                            link.style.borderRadius = "5px";
                            link.style.textDecoration = "none";
                            
                            // Add a message that explains the issue
                            const message = document.createElement('div');
                            message.innerHTML = `
                                <div style="text-align:center; padding:20px; margin-top:20px;">
                                    <h3 style="color:#333; margin-bottom:10px;">Navigation Issue Detected</h3>
                                    <p style="color:#666; margin-bottom:20px;">We're having trouble automatically taking you to the next step.</p>
                                </div>
                            `;
                            
                            // Clear the content and show the manual link
                            document.body.innerHTML = '';
                            document.body.appendChild(message);
                            document.body.appendChild(link);
                            
                            // Automatically click the link
                            console.log("NAVIGATION: Auto-clicking fallback link");
                            link.click();
                        }, 1000);
                    }, 1000);
                } catch (navError) {
                    console.error("NAVIGATION ERROR:", navError);
                    console.error("Navigation error stack:", navError.stack);
                    showError("Error navigating to the next step. Please try again.");
                }
            })
            .catch(error => {
                console.error('ERROR in fetch:', error);
                console.error('Stack trace:', error.stack);
                showError('There was an error processing your audio. Please try again.');
                
                // Re-enable button
                submitButton.disabled = false;
                submitButton.classList.remove('opacity-75', 'cursor-not-allowed');
                
                // Check if arrowIcon exists before trying to use it
                if (arrowIcon) {
                    arrowIcon.classList.remove('hidden');
                } else {
                    console.warn("UI: arrowIcon is null, skipping show operation in error handler");
                }
                
                // Check if spinner exists before trying to use it
                if (spinner) {
                    spinner.classList.add('hidden');
                } else {
                    console.warn("UI: spinner is null, skipping hide operation in error handler");
                }
                
                // Change text back
                if (buttonText) {
                    buttonText.textContent = 'Continue';
                } else {
                    console.warn("UI: buttonText is null, skipping text update in error handler");
                }
            });
        } else {
            console.warn("submitForm called but conditions not met:");
            console.warn("- audioMode:", audioMode);
            console.warn("- audioRecommendations.value:", audioRecommendations.value ? "exists (length: " + audioRecommendations.value.length + ")" : "missing");
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