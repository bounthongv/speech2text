console.log('JavaScript file loaded - FULL VERSION');

document.addEventListener("DOMContentLoaded", function () {
  console.log('DOM Content Loaded - FULL VERSION');

  // DOM Elements
  const recordButton = document.getElementById("recordButton");
  const recordButtonText = document.getElementById("recordButtonText");
  const recordingStatus = document.getElementById("recordingStatus");
  const transcriptionResult = document.getElementById("transcriptionResult");
  const streamingTranscription = document.getElementById("streamingTranscription");
  const liveTranscriptText = document.getElementById("liveTranscriptText");
  const alertArea = document.getElementById("alertArea");
  const audioVisualizer = document.getElementById("audioVisualizer");
  const calibrateBtn = document.getElementById("calibrateBtn");
  const measureNoiseBtn = document.getElementById("measureNoiseBtn");
  const streamingMode = document.getElementById("streamingMode");
  const recordingOptions = document.getElementById("recordingOptions");
  const recordingTimeLimit = document.getElementById("recordingTimeLimit");
  const timeLimitDisplay = document.getElementById("timeLimitDisplay");
  const recordingTimer = document.getElementById("recordingTimer");
  const timerDisplay = document.getElementById("timerDisplay");
  const timerProgress = document.getElementById("timerProgress");
  const remainingTime = document.getElementById("remainingTime");
  const modeDescription = document.getElementById("modeDescription");
  const transcriptionEditorTab = document.getElementById("transcription-editor-tab") ?
    new bootstrap.Tab(document.getElementById("transcription-editor-tab")) : null;
  const editor = document.getElementById("editor");

  // Recording state
  let isRecording = false;
  let mediaRecorder = null;
  let recordedChunks = [];
  let isStreamingMode = true; // true = live transcription, false = recording mode
  let speechRecognition = null;

  // Recording timer variables
  let recordingStartTime = null;
  let recordingTimerInterval = null;
  let maxRecordingTime = 10 * 60 * 1000; // Default 10 minutes in milliseconds

  // Streaming state
  let socket = null;
  let streamingSessionId = null;
  let audioChunkCounter = 0;
  let transcriptChunks = [];
  let completeFinalTranscript = '';
  let lastInterimElement = null;
  let processedResultsCount = 0;
  let recognitionRestartCount = 0;

  // Memory management for long sessions
  const MAX_CHUNKS = 1000; // Limit chunks to prevent memory issues
  const MAX_TRANSCRIPT_LENGTH = 50000; // Limit transcript length (characters)
  const CLEANUP_INTERVAL = 300000; // Clean up every 5 minutes (300000ms)
  let sessionStartTime = null;
  let cleanupInterval = null;

  // Usage tracking
  let currentUsage = null;
  let usageLimitExceeded = false;

  // Visualization variables
  let stream = null;
  let audioContext = null;
  let analyser = null;
  let visualizationId = null;

  // Initialize
  initializeApp();

  function initializeApp() {
    console.log('Initializing app...');
    console.log('Elements found:', {
      recordButton: !!recordButton,
      calibrateBtn: !!calibrateBtn,
      measureNoiseBtn: !!measureNoiseBtn,
      streamingMode: !!streamingMode
    });

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showAlert(
        "danger",
        "<i class='fas fa-exclamation-triangle'></i> Your browser does not support audio recording. Please use a modern browser like Chrome or Firefox."
      );
      recordButton.disabled = true;
      updateTranscriptionStatus('error', 'Browser not supported');
      return;
    }

    // Initialize Socket.IO with delay to ensure it's loaded
    setTimeout(() => {
      try {
        initializeSocket();
      } catch (error) {
        console.error('Socket.IO initialization failed:', error);
      }
    }, 1000); // Wait 1 second for Socket.IO to load

    // Event listeners
    if (recordButton) {
      recordButton.addEventListener("click", toggleRecording);
      console.log('Record button listener added');
    }
    if (calibrateBtn) {
      calibrateBtn.addEventListener("click", calibrateMicrophone);
      console.log('Calibrate button listener added');
    }
    if (measureNoiseBtn) {
      measureNoiseBtn.addEventListener("click", measureNoise);
      console.log('Measure noise button listener added');
    }
    // Mode selection listeners
    if (streamingMode) {
      streamingMode.addEventListener("change", handleModeChange);
      console.log('Streaming mode listener added');
    }

    // Recording time limit slider
    if (recordingTimeLimit) {
      recordingTimeLimit.addEventListener("input", updateTimeLimitDisplay);
      console.log('Recording time limit listener added');
    }

    // Copy and Cut button listeners
    const copyBtn = document.getElementById('copyBtn');
    const cutBtn = document.getElementById('cutBtn');

    if (copyBtn) {
      copyBtn.addEventListener('click', copyTranscription);
      console.log('Copy button listener added');
    }
    if (cutBtn) {
      cutBtn.addEventListener('click', cutTranscription);
      console.log('Cut button listener added');
    }

    // Initialize UI
    updateTranscriptionStatus('ready', 'Ready to transcribe');
    handleModeChange(); // Set initial mode
    updateUsageDisplay(); // Load current usage status
    console.log('App initialization complete');
  }

  function initializeSocket() {
    console.log('Initializing Socket.IO...');
    if (typeof io === 'undefined') {
      console.error('Socket.IO library not loaded, retrying in 2 seconds...');

      // Retry after 2 seconds
      setTimeout(() => {
        if (typeof io === 'undefined') {
          console.error('Socket.IO library still not loaded after retry');
          showAlert("warning", "<i class='fas fa-exclamation-triangle'></i> Socket.IO failed to load. Real-time streaming unavailable. Please refresh the page.");
        } else {
          console.log('Socket.IO loaded on retry, initializing...');
          initializeSocket();
        }
      }, 2000);
      return;
    }

    try {
      socket = io();
      console.log('Socket.IO client created');

      socket.on('connect', function() {
        console.log('✅ Connected to server via Socket.IO');
        console.log('Socket ID:', socket.id);
      });

      socket.on('disconnect', function() {
        console.log('❌ Disconnected from server');
        if (isRecording && isStreamingMode) {
          stopRecording();
        }
      });

      socket.on('connect_error', function(error) {
        console.error('❌ Socket.IO connection error:', error);
        showAlert("danger", "<i class='fas fa-exclamation-triangle'></i> Connection error. Streaming mode unavailable.");
      });
    } catch (error) {
      console.error('Error initializing Socket.IO:', error);
      showAlert("danger", "<i class='fas fa-exclamation-triangle'></i> Failed to initialize real-time connection.");
    }

    socket.on('streaming_started', function(data) {
      streamingSessionId = data.session_id;
      console.log('Streaming session started:', streamingSessionId);
    });

    socket.on('transcription_chunk', function(data) {
      handleTranscriptionChunk(data);
    });

    socket.on('streaming_stopped', function(data) {
      console.log('Streaming session stopped');
      streamingSessionId = null;

      // Update usage if provided
      if (data.minutes_used) {
        updateUsageDisplay(data.total_usage);
        showAlert('info', `<i class="fas fa-clock"></i> Session completed. Used ${data.minutes_used} minutes.`);
      }
    });

    socket.on('usage_limit_exceeded', function(data) {
      console.log('Usage limit exceeded');
      usageLimitExceeded = true;
      showUsageLimitModal(data);
    });

    socket.on('streaming_error', function(data) {
      console.error('Streaming error:', data);
      showAlert('danger', `<i class='fas fa-exclamation-triangle'></i> Streaming Error: ${data.message}`);
      if (isRecording) {
        stopRecording();
      }
    });

    socket.on('audio_quality_warning', function(data) {
      console.warn('Audio quality warning:', data);
      showAlert('warning', `<i class='fas fa-volume-down'></i> Audio Quality: ${data.message}`);
    });
  }

  function handleModeChange() {
    isStreamingMode = streamingMode.checked;

    if (isStreamingMode) {
      // Live Transcription Mode (Switch ON)
      recordButtonText.textContent = "Start Live Transcription";
      modeDescription.textContent = "Live transcription with instant results";
      recordingOptions.style.display = "none";
      recordingTimer.style.display = "none";
      streamingTranscription.style.display = "block";
      transcriptionResult.style.display = "block"; // Show both for live mode
      recordButton.innerHTML = '<i class="fas fa-broadcast-tower"></i> <span id="recordButtonText">Start Live Transcription</span>';
    } else {
      // Recording Mode (Switch OFF)
      recordButtonText.textContent = "Start Recording";
      modeDescription.textContent = "Time-limited recording with final transcript";
      recordingOptions.style.display = "block";
      recordingTimer.style.display = "none";
      streamingTranscription.style.display = "none"; // Hide live transcript in record mode
      transcriptionResult.style.display = "block";
      recordButton.innerHTML = '<i class="fas fa-microphone"></i> <span id="recordButtonText">Start Recording</span>';

      // Update max recording time and display
      updateRecordingTimeLimit();
      updateTimeLimitDisplay();
    }
  }

  function updateTimeLimitDisplay() {
    if (recordingTimeLimit && timeLimitDisplay) {
      const minutes = recordingTimeLimit.value;
      timeLimitDisplay.textContent = `${minutes}min`;
    }
  }

  function updateRecordingTimeLimit() {
    if (recordingTimeLimit) {
      const minutes = parseInt(recordingTimeLimit.value);
      maxRecordingTime = minutes * 60 * 1000; // Convert to milliseconds
      console.log(`Recording time limit set to ${minutes} minutes`);
    }
  }

  function startRecordingTimer() {
    if (!isStreamingMode) {
      recordingStartTime = Date.now();
      recordingTimer.style.display = "block";

      recordingTimerInterval = setInterval(() => {
        const elapsed = Date.now() - recordingStartTime;
        const remaining = maxRecordingTime - elapsed;

        if (remaining <= 0) {
          // Time limit reached, stop recording
          stopRecording();
          showAlert('warning', '<i class="fas fa-clock"></i> Recording time limit reached. Recording stopped automatically.');
          return;
        }

        // Update timer display
        const elapsedMinutes = Math.floor(elapsed / 60000);
        const elapsedSeconds = Math.floor((elapsed % 60000) / 1000);
        const remainingMinutes = Math.floor(remaining / 60000);
        const remainingSeconds = Math.floor((remaining % 60000) / 1000);

        timerDisplay.textContent = `${elapsedMinutes.toString().padStart(2, '0')}:${elapsedSeconds.toString().padStart(2, '0')}`;
        remainingTime.textContent = `${remainingMinutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;

        // Update progress bar
        const progressPercent = (elapsed / maxRecordingTime) * 100;
        timerProgress.style.width = `${progressPercent}%`;

        // Change color when time is running low
        if (remaining < 60000) { // Less than 1 minute
          timerProgress.classList.remove('bg-danger');
          timerProgress.classList.add('bg-warning');
        }
        if (remaining < 30000) { // Less than 30 seconds
          timerProgress.classList.remove('bg-warning');
          timerProgress.classList.add('bg-danger');
        }
      }, 1000);
    }
  }

  function stopRecordingTimer() {
    if (recordingTimerInterval) {
      clearInterval(recordingTimerInterval);
      recordingTimerInterval = null;
    }
    recordingTimer.style.display = "none";
    recordingStartTime = null;
  }

  function toggleRecording() {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }

  async function startRecording() {
    try {
      console.log('Starting recording, streaming mode:', isStreamingMode);

      // Check Socket.IO connection for streaming mode
      if (isStreamingMode && (!socket || !socket.connected)) {
        console.error('Socket.IO not connected for streaming mode');
        showAlert("danger", "<i class='fas fa-exclamation-triangle'></i> Connection error. Please refresh the page and try again.");
        return;
      }

      // Update recording time limit for recording mode
      if (!isStreamingMode) {
        updateRecordingTimeLimit();
      }

      console.log('Requesting microphone access...');
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      });

      console.log('Microphone access granted');
      isRecording = true;
      recordedChunks = [];
      transcriptChunks = [];

      // Start memory management for long sessions
      startMemoryManagement();

      if (isStreamingMode) {
        console.log('Starting streaming transcription...');
        startStreamingTranscription();
      } else {
        console.log('Starting traditional recording...');
        startTraditionalRecording();
        startRecordingTimer();
      }

      const stopText = isStreamingMode ? "Stop Live Transcription" : "Stop Recording";
      recordButton.innerHTML = `<i class='fas fa-stop'></i> ${stopText}`;
      recordButton.classList.remove("btn-primary");
      recordButton.classList.add("btn-danger");

      const modeText = isStreamingMode ? "Live transcription" : "Recording";
      recordingStatus.innerHTML = `
        <div class='alert alert-info d-flex align-items-center'>
          <div class="spinner-border spinner-border-sm me-3" role="status">
            <span class="visually-hidden">${modeText}...</span>
          </div>
          <div>
            <strong>${modeText} in progress...</strong>
            <div class="small">
              ${isStreamingMode ?
                '<i class="fas fa-lightbulb text-warning"></i> Tip: Wait 2-3 seconds after starting before speaking for best results' :
                'Speak clearly into your microphone'
              }
            </div>
          </div>
        </div>
      `;

      updateTranscriptionStatus('recording', `${modeText}...`);
      startVisualization(stream);

    } catch (err) {
      console.error("Error starting recording:", err);
      console.error("Error details:", err.name, err.message);

      let errorMessage = "Could not start recording. ";
      if (err.name === 'NotAllowedError') {
        errorMessage += "Please allow microphone access and try again.";
      } else if (err.name === 'NotFoundError') {
        errorMessage += "No microphone found. Please connect a microphone.";
      } else if (err.name === 'NotSupportedError') {
        errorMessage += "Your browser doesn't support audio recording.";
      } else {
        errorMessage += `Error: ${err.message}`;
      }

      updateTranscriptionStatus('error', 'Microphone access denied');
      showAlert(
        "danger",
        `<i class='fas fa-exclamation-triangle'></i> ${errorMessage}`
      );
    }
  }

  function startStreamingTranscription() {
    console.log('Starting hybrid streaming transcription...');

    // Reset transcript variables for new session
    completeFinalTranscript = '';
    lastInterimElement = null;
    processedResultsCount = 0;
    recognitionRestartCount = 0;

    // Remove any existing session summary - commented out since we're hiding session summary
    // const existingSummary = document.getElementById('sessionSummary');
    // if (existingSummary) {
    //   existingSummary.remove();
    // }

    // Start backend streaming session
    startBackendStreaming();

    // Also start browser speech recognition as backup/supplement
    startBrowserSpeechRecognition();
  }

  function startBackendStreaming() {
    console.log('Starting backend audio streaming...');

    // Start streaming session with backend
    socket.emit('start_streaming', {
      use_calibration: false,
      use_phrases: false
    });

    // Start continuous audio capture and streaming
    startContinuousAudioCapture();
  }

  function startContinuousAudioCapture() {
    if (!stream) {
      console.error('No audio stream available for continuous capture');
      return;
    }

    // Create MediaRecorder for continuous audio streaming
    const options = {
      mimeType: 'audio/webm;codecs=opus',
      audioBitsPerSecond: 16000
    };

    try {
      const mediaRecorder = new MediaRecorder(stream, options);

      // Capture smaller, more frequent chunks (250ms each)
      const chunkInterval = 250; // milliseconds

      mediaRecorder.ondataavailable = function(event) {
        if (event.data.size > 0 && streamingSessionId) {
          // Convert blob to base64 and send to backend
          const reader = new FileReader();
          reader.onload = function() {
            const base64Data = reader.result.split(',')[1];
            socket.emit('audio_chunk', {
              session_id: streamingSessionId,
              audio_data: base64Data
            });
          };
          reader.readAsDataURL(event.data);
        }
      };

      mediaRecorder.onerror = function(event) {
        console.error('MediaRecorder error:', event.error);
      };

      // Start recording with frequent chunks
      mediaRecorder.start(chunkInterval);

      // Store reference for cleanup
      window.continuousRecorder = mediaRecorder;

      console.log('Continuous audio capture started with', chunkInterval, 'ms chunks');

    } catch (error) {
      console.error('Failed to start continuous audio capture:', error);
      // Fall back to browser-only speech recognition
      startBrowserSpeechRecognition();
    }
  }

  function startBrowserSpeechRecognition() {
    // Check if browser supports Web Speech API
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      console.log('Browser speech recognition not available');
      return;
    }

    console.log('Starting browser speech recognition as supplement...');

    // Use browser's built-in speech recognition for real-time transcription
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    speechRecognition = new SpeechRecognition();

    // Optimize for Lao language speech recognition
    speechRecognition.continuous = true;
    speechRecognition.interimResults = true;
    speechRecognition.lang = 'lo-LA'; // Lao language
    speechRecognition.maxAlternatives = 3; // Get multiple alternatives for better accuracy

    // Additional optimizations for Lao speech patterns
    if (speechRecognition.serviceURI) {
      speechRecognition.serviceURI = 'https://www.google.com/speech-api/v2/recognize';
    }

    let finalTranscript = '';

    speechRecognition.onresult = function(event) {
      let interimTranscript = '';
      let hasNewFinalResults = false;

      // Process all results, but only add new final results
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0].transcript;
        const confidence = result[0].confidence || 0.8;

        if (result.isFinal) {
          // Only process final results we haven't seen before
          if (i >= processedResultsCount) {
            // Apply confidence threshold for Lao language
            if (confidence >= 0.6) { // Lower threshold for Lao
              addFinalTranscript(transcript.trim());
              hasNewFinalResults = true;
            } else {
              console.log(`Low confidence result skipped: ${transcript} (${confidence})`);
            }
            processedResultsCount = i + 1;
          }
        } else {
          // Collect all interim results (they replace each other)
          interimTranscript += transcript;
        }
      }

      // Update interim only if no new final results (to avoid flicker)
      if (!hasNewFinalResults) {
        updateInterimTranscript(interimTranscript);
      }
    };

    speechRecognition.onerror = function(event) {
      console.error('Speech recognition error:', event.error);
      if (event.error === 'not-allowed') {
        showAlert("danger", "<i class='fas fa-microphone-slash'></i> Microphone access denied. Please allow microphone access and try again.");
      } else {
        showAlert("warning", "<i class='fas fa-exclamation-triangle'></i> Speech recognition error: " + event.error);
      }
    };

    speechRecognition.onend = function() {
      if (isRecording) {
        // Restart if still recording, but track restarts to prevent runaway
        recognitionRestartCount++;
        if (recognitionRestartCount < 30) { // Reduced restart limit
          try {
            setTimeout(() => {
              if (isRecording && speechRecognition) {
                // Reset processed count when restarting (new recognition session)
                processedResultsCount = 0;
                speechRecognition.start();
              }
            }, 500); // Increased delay to prevent rapid restarts and reduce duplicates
          } catch (err) {
            console.log('Speech recognition ended, not restarting due to error:', err);
          }
        } else {
          console.log('Too many restarts, stopping speech recognition');
          showAlert('warning', '<i class="fas fa-exclamation-triangle"></i> Speech recognition restarted too many times. Please stop and start again.');
          stopRecording();
        }
      }
    };

    try {
      speechRecognition.start();
      console.log('Browser speech recognition started');
    } catch (err) {
      console.error('Error starting speech recognition:', err);
      showAlert("danger", "<i class='fas fa-exclamation-triangle'></i> Failed to start speech recognition.");
    }

    // Clear live transcript with initialization guidance
    liveTranscriptText.innerHTML = `
      <div class="text-center text-muted">
        <i class="fas fa-microphone fa-2x mb-3"></i>
        <p class="mb-0">Initializing speech recognition...</p>
        <small class="text-warning">
          <i class="fas fa-info-circle"></i>
          Please wait 2-3 seconds before speaking for best results
        </small>
      </div>
    `;

    // Update message after initialization
    setTimeout(() => {
      if (isRecording && liveTranscriptText.innerHTML.includes('Initializing')) {
        liveTranscriptText.innerHTML = `
          <div class="text-center text-muted">
            <i class="fas fa-microphone fa-2x mb-3 text-success"></i>
            <p class="mb-0">Ready! Start speaking...</p>
            <small class="text-success">
              <i class="fas fa-check-circle"></i>
              System is ready for transcription
            </small>
          </div>
        `;
      }
    }, 2500);
  }

  function addFinalTranscript(text) {
    // Clear initial message if needed
    const existingContent = liveTranscriptText.innerHTML;
    if (existingContent.includes('Listening for speech')) {
      liveTranscriptText.innerHTML = '';
    }

    // Check for duplicates
    if (isDuplicateText(text)) {
      console.log('Duplicate text detected on frontend, skipping:', text);
      return;
    }

    // Remove any existing interim element when adding final text
    if (lastInterimElement && lastInterimElement.parentNode) {
      lastInterimElement.parentNode.removeChild(lastInterimElement);
      lastInterimElement = null;
    }

    // Add to complete transcript
    completeFinalTranscript += text + ' ';

    // Create chunk element for live transcript
    const chunkElement = document.createElement('span');
    chunkElement.className = 'transcript-chunk';
    chunkElement.textContent = text + ' ';

    liveTranscriptText.appendChild(chunkElement);

    // Auto-scroll and update summary
    liveTranscriptText.scrollTop = liveTranscriptText.scrollHeight;
    // updateSessionSummary(); // Hidden for now - may need later
    updateTranscriptionResult();
  }

  function isDuplicateText(newText) {
    if (!newText || !newText.trim()) {
      return true;
    }

    const cleanNewText = newText.trim().toLowerCase();

    // Check against recent final transcript
    const recentTranscript = completeFinalTranscript.trim().toLowerCase();
    if (recentTranscript.endsWith(cleanNewText)) {
      return true;
    }

    // Check if new text is already contained in recent transcript
    const words = recentTranscript.split(' ');
    const recentWords = words.slice(-10).join(' '); // Check last 10 words

    if (recentWords.includes(cleanNewText)) {
      return true;
    }

    return false;
  }

  function updateInterimTranscript(text) {
    // Remove previous interim element if it exists
    if (lastInterimElement && lastInterimElement.parentNode) {
      lastInterimElement.parentNode.removeChild(lastInterimElement);
      lastInterimElement = null;
    }

    // Only add interim if there's text and we're not showing initial message
    if (text && text.trim()) {
      // Clear initial message if needed
      const existingContent = liveTranscriptText.innerHTML;
      if (existingContent.includes('Listening for speech')) {
        liveTranscriptText.innerHTML = '';
      }

      // Remove previous interim element
      if (lastInterimElement && lastInterimElement.parentNode) {
        lastInterimElement.parentNode.removeChild(lastInterimElement);
      }

      // Create new interim element
      lastInterimElement = document.createElement('span');
      lastInterimElement.className = 'transcript-chunk interim-text';
      lastInterimElement.textContent = text.trim() + ' ';

      liveTranscriptText.appendChild(lastInterimElement);

      // Auto-scroll
      liveTranscriptText.scrollTop = liveTranscriptText.scrollHeight;
    }
  }

  function updateTranscriptionResult() {
    const transcriptionResult = document.getElementById('transcriptionResult');
    const transcriptionActions = document.getElementById('transcriptionActions');

    if (completeFinalTranscript.trim()) {
      transcriptionResult.innerHTML = `<div style="white-space: pre-wrap; word-wrap: break-word;">${completeFinalTranscript}</div>`;
      transcriptionActions.style.display = 'block';
    } else {
      transcriptionResult.innerHTML = `
        <div class="text-center text-muted">
          <i class="fas fa-microphone-slash fa-2x mb-3"></i>
          <p class="mb-0">No transcription yet...</p>
          <small>Start recording to see your speech converted to text</small>
        </div>
      `;
      transcriptionActions.style.display = 'none';
    }
  }

  function copyTranscription() {
    if (completeFinalTranscript.trim()) {
      navigator.clipboard.writeText(completeFinalTranscript.trim()).then(() => {
        showAlert('success', '<i class="fas fa-copy"></i> Transcription copied to clipboard!');
      }).catch(err => {
        console.error('Failed to copy text: ', err);
        showAlert('danger', '<i class="fas fa-exclamation-triangle"></i> Failed to copy to clipboard');
      });
    }
  }

  function cutTranscription() {
    if (completeFinalTranscript.trim()) {
      navigator.clipboard.writeText(completeFinalTranscript.trim()).then(() => {
        // Clear the transcription
        completeFinalTranscript = '';
        transcriptChunks = [];
        liveTranscriptText.innerHTML = `
          <div class="text-center text-muted">
            <i class="fas fa-microphone fa-2x mb-3"></i>
            <p class="mb-0">Listening for speech...</p>
            <small>Start speaking to see real-time transcription</small>
          </div>
        `;
        updateTranscriptionResult();
        showAlert('success', '<i class="fas fa-cut"></i> Transcription cut to clipboard!');
      }).catch(err => {
        console.error('Failed to cut text: ', err);
        showAlert('danger', '<i class="fas fa-exclamation-triangle"></i> Failed to cut to clipboard');
      });
    }
  }

  // Memory management for long sessions
  function cleanupMemory() {
    console.log('Performing memory cleanup...');

    // Limit transcript chunks
    if (transcriptChunks.length > MAX_CHUNKS) {
      const excessChunks = transcriptChunks.length - MAX_CHUNKS;
      transcriptChunks.splice(0, excessChunks);
      console.log(`Removed ${excessChunks} old chunks`);
    }

    // Limit transcript length
    if (completeFinalTranscript.length > MAX_TRANSCRIPT_LENGTH) {
      const words = completeFinalTranscript.split(' ');
      const excessWords = Math.floor(words.length * 0.2); // Remove 20% of oldest words
      completeFinalTranscript = words.slice(excessWords).join(' ');
      console.log(`Trimmed ${excessWords} words from transcript`);
      updateTranscriptionResult();
    }

    // Clean up DOM elements in live transcript if too many
    const liveChunks = liveTranscriptText.querySelectorAll('.transcript-chunk');
    if (liveChunks.length > 50) {
      const excessElements = liveChunks.length - 50;
      for (let i = 0; i < excessElements; i++) {
        liveChunks[i].remove();
      }
      console.log(`Removed ${excessElements} old live transcript elements`);
    }
  }

  function startMemoryManagement() {
    sessionStartTime = Date.now();

    // Set up periodic cleanup
    if (cleanupInterval) {
      clearInterval(cleanupInterval);
    }

    cleanupInterval = setInterval(() => {
      cleanupMemory();

      // Show session duration info
      const duration = Math.floor((Date.now() - sessionStartTime) / 60000); // minutes
      console.log(`Session running for ${duration} minutes`);

      if (duration > 60) { // After 1 hour
        showAlert('info', `<i class="fas fa-clock"></i> Session running for ${duration} minutes. Consider saving your transcription.`);
      }
    }, CLEANUP_INTERVAL);

    console.log('Memory management started');
  }

  function stopMemoryManagement() {
    if (cleanupInterval) {
      clearInterval(cleanupInterval);
      cleanupInterval = null;
    }
    sessionStartTime = null;
    console.log('Memory management stopped');
  }

  // User registration functions
  function showEmailModal() {
    const modal = new bootstrap.Modal(document.getElementById('emailModal'));
    modal.show();
  }

  function registerEmail() {
    const email = document.getElementById('userEmail').value.trim();

    if (!email || !email.includes('@')) {
      showAlert('danger', '<i class="fas fa-exclamation-triangle"></i> Please enter a valid email address');
      return;
    }

    fetch('/register_email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        showAlert('success', `<i class="fas fa-check-circle"></i> ${data.message}`);
        updateUsageDisplay();
        bootstrap.Modal.getInstance(document.getElementById('emailModal')).hide();

        // Hide email upgrade button
        const emailUpgrade = document.getElementById('emailUpgrade');
        if (emailUpgrade) {
          emailUpgrade.style.display = 'none';
        }
      } else {
        showAlert('danger', `<i class="fas fa-exclamation-triangle"></i> ${data.message}`);
      }
    })
    .catch(error => {
      console.error('Error registering email:', error);
      showAlert('danger', '<i class="fas fa-exclamation-triangle"></i> Failed to register email');
    });
  }

  function updateUsageDisplay() {
    fetch('/usage_status')
    .then(response => response.json())
    .then(data => {
      const usageProgress = document.getElementById('usageProgress');
      const usageText = document.getElementById('usageText');

      if (usageProgress && usageText) {
        let progressPercent = 0;
        let displayText = '';

        if (data.monthly_limit === 'Unlimited') {
          progressPercent = 0;
          displayText = `${data.minutes_used} min / Unlimited`;
          usageProgress.classList.remove('bg-primary', 'bg-warning', 'bg-danger');
          usageProgress.classList.add('bg-success');
        } else {
          progressPercent = (data.minutes_used / data.monthly_limit) * 100;
          displayText = `${data.minutes_used}/${data.monthly_limit} min`;

          // Update progress bar color based on usage
          usageProgress.classList.remove('bg-primary', 'bg-warning', 'bg-danger', 'bg-success');
          if (progressPercent >= 90) {
            usageProgress.classList.add('bg-danger');
          } else if (progressPercent >= 70) {
            usageProgress.classList.add('bg-warning');
          } else {
            usageProgress.classList.add('bg-primary');
          }
        }

        usageProgress.style.width = `${Math.min(progressPercent, 100)}%`;
        usageText.textContent = displayText;
      }
    })
    .catch(error => {
      console.error('Error updating usage display:', error);
    });
  }

  // Session Summary functionality - commented out for cleaner interface
  // May be needed later, so keeping the code
  /*
  function updateSessionSummary() {
    // Create session summary if it doesn't exist
    if (!document.getElementById('sessionSummary')) {
      const summaryDiv = document.createElement('div');
      summaryDiv.id = 'sessionSummary';
      summaryDiv.className = 'mt-4 p-3 border rounded bg-light';

      const summaryTitle = document.createElement('h6');
      summaryTitle.innerHTML = '<i class="fas fa-clipboard-list"></i> Session Summary';
      summaryTitle.className = 'mb-2';

      const fullTranscriptLabel = document.createElement('div');
      fullTranscriptLabel.className = 'text-muted small mb-1';
      fullTranscriptLabel.textContent = 'Full Transcript:';

      const fullTranscriptText = document.createElement('div');
      fullTranscriptText.id = 'fullTranscriptText';
      fullTranscriptText.className = 'mb-2';

      const statsDiv = document.createElement('div');
      statsDiv.id = 'transcriptionStats';
      statsDiv.className = 'text-muted small';

      summaryDiv.appendChild(summaryTitle);
      summaryDiv.appendChild(fullTranscriptLabel);
      summaryDiv.appendChild(fullTranscriptText);
      summaryDiv.appendChild(statsDiv);

      liveTranscriptText.parentNode.appendChild(summaryDiv);
    }

    // Update the summary content
    const fullTranscriptText = document.getElementById('fullTranscriptText');
    const statsDiv = document.getElementById('transcriptionStats');

    if (fullTranscriptText && completeFinalTranscript) {
      fullTranscriptText.textContent = completeFinalTranscript.trim();

      // Calculate stats
      const words = completeFinalTranscript.trim().split(/\s+/).length;
      statsDiv.innerHTML = `<i class="fas fa-chart-bar"></i> Chunks: ${document.querySelectorAll('.transcript-chunk:not(.interim-text)').length} | Words: ${words}`;
    }
  }
  */

  function startTraditionalRecording() {
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = function (e) {
      if (e.data.size > 0) {
        recordedChunks.push(e.data);
      }
    };

    mediaRecorder.onstop = uploadRecording;
    mediaRecorder.start();
  }

  function handleTranscriptionChunk(data) {
    if (data.text && data.text.trim()) {
      const confidence = data.confidence || 0.5;
      const confidenceClass = confidence > 0.8 ? 'high' : confidence > 0.5 ? 'medium' : 'low';

      // Add to complete transcript
      completeFinalTranscript += data.text + ' ';

      // Create chunk element for live transcript
      const chunkElement = document.createElement('span');
      chunkElement.className = `transcript-chunk confidence-${confidenceClass}`;
      chunkElement.textContent = data.text + ' ';

      // Clear initial message if needed
      const existingContent = liveTranscriptText.innerHTML;
      if (existingContent.includes('Listening for speech')) {
        liveTranscriptText.innerHTML = '';
      }

      liveTranscriptText.appendChild(chunkElement);

      // Auto-scroll to bottom
      liveTranscriptText.scrollTop = liveTranscriptText.scrollHeight;

      // Store chunk
      transcriptChunks.push({
        text: data.text,
        confidence: confidence,
        timestamp: Date.now(),
        chunk_id: data.chunk_id
      });

      // Update stats and main result
      updateStreamingStats();
      updateTranscriptionResult();
    }
  }

  function updateStreamingStats() {
    const totalChunks = transcriptChunks.length;
    if (totalChunks === 0) return;

    const avgConfidence = transcriptChunks.reduce((sum, chunk) => sum + chunk.confidence, 0) / totalChunks;
    const totalWords = transcriptChunks.reduce((sum, chunk) => sum + chunk.text.split(' ').length, 0);

    let statsElement = document.getElementById('streamingStats');
    if (!statsElement) {
      statsElement = document.createElement('div');
      statsElement.id = 'streamingStats';
      statsElement.className = 'streaming-stats';
      liveTranscriptText.parentNode.appendChild(statsElement);
    }

    statsElement.innerHTML = `
      <i class="fas fa-chart-line"></i>
      Chunks: ${totalChunks} |
      Words: ${totalWords} |
      Avg. Confidence: ${(avgConfidence * 100).toFixed(1)}%
    `;
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
    }

    // Stop continuous recorder if active
    if (window.continuousRecorder && window.continuousRecorder.state === "recording") {
      window.continuousRecorder.stop();
      window.continuousRecorder = null;
    }

    // Stop speech recognition if active
    if (speechRecognition) {
      speechRecognition.stop();
      speechRecognition = null;
    }

    isRecording = false;

    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }

    stopVisualization();
    stopRecordingTimer(); // Stop the recording timer
    stopMemoryManagement(); // Stop memory management

    // Update button
    recordButton.innerHTML = `<i class='fas fa-microphone'></i> ${recordButtonText.textContent}`;
    recordButton.classList.remove("btn-danger");
    recordButton.classList.add("btn-primary");

    if (isStreamingMode) {
      stopStreamingTranscription();
    } else {
      recordingStatus.innerHTML = `
        <div class='alert alert-warning d-flex align-items-center'>
          <div class="spinner-border spinner-border-sm me-3" role="status">
            <span class="visually-hidden">Processing...</span>
          </div>
          <div>
            <strong>Processing audio...</strong>
            <div class="small">Converting speech to text, please wait</div>
          </div>
        </div>
      `;
      updateTranscriptionStatus('processing', 'Processing audio...');
    }
  }

  function stopStreamingTranscription() {
    if (streamingSessionId) {
      socket.emit('stop_streaming', {
        session_id: streamingSessionId
      });
    }

    recordingStatus.innerHTML = `
      <div class='alert alert-success d-flex align-items-center'>
        <i class="fas fa-check-circle me-3"></i>
        <div>
          <strong>Live transcription completed</strong>
          <div class="small">Session ended successfully</div>
        </div>
      </div>
    `;

    updateTranscriptionStatus('completed', 'Live transcription completed');

    // Show final transcript summary
    if (transcriptChunks.length > 0) {
      const fullText = transcriptChunks.map(chunk => chunk.text).join(' ');
      const avgConfidence = transcriptChunks.reduce((sum, chunk) => sum + chunk.confidence, 0) / transcriptChunks.length;

      // Add final summary to live transcript
      const summaryElement = document.createElement('div');
      summaryElement.className = 'mt-3 p-3 bg-light border rounded';
      summaryElement.innerHTML = `
        <h6><i class="fas fa-file-alt"></i> Session Summary</h6>
        <p><strong>Full Transcript:</strong> ${fullText}</p>
        <small class="text-muted">
          Total chunks: ${transcriptChunks.length} |
          Average confidence: ${(avgConfidence * 100).toFixed(1)}%
        </small>
      `;
      liveTranscriptText.appendChild(summaryElement);
    }

    streamingSessionId = null;
    audioChunkCounter = 0;
  }

  async function calibrateMicrophone() {
    console.log('Calibrate microphone function called');
    try {
      // Update button state
      const originalText = calibrateBtn.innerHTML;
      calibrateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calibrating...';
      calibrateBtn.disabled = true;

      showAlert(
        "info",
        "Starting microphone calibration... Please speak at a normal volume for a few seconds."
      );

      const response = await fetch("/calibrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "calibrate" }),
      });

      const result = await response.json();

      if (result.status === "success") {
        const calibration = result.calibration;
        const calibrationHtml = `
          <div class="calibration-results">
            <h6><i class="fas fa-check-circle text-success"></i> Microphone Calibration Complete!</h6>
            <div class="row mt-3">
              <div class="col-md-4">
                <div class="metric-card">
                  <div class="metric-label">Optimal Gain</div>
                  <div class="metric-value">${calibration.gain.toFixed(2)}</div>
                </div>
              </div>
              <div class="col-md-4">
                <div class="metric-card">
                  <div class="metric-label">Noise Threshold</div>
                  <div class="metric-value">${calibration.noise_threshold.toFixed(4)}</div>
                </div>
              </div>
              <div class="col-md-4">
                <div class="metric-card">
                  <div class="metric-label">Peak Amplitude</div>
                  <div class="metric-value">${calibration.peak_amplitude.toFixed(3)}</div>
                </div>
              </div>
            </div>
            <div class="mt-2">
              <small class="text-muted">
                <i class="fas fa-info-circle"></i> Your microphone is now optimized for speech recognition
              </small>
            </div>
          </div>
        `;

        showAlert("success", calibrationHtml);
        document.getElementById("recordButton").disabled = false;

        // Update calibration status in the card
        updateCalibrationStatus('calibrated', calibration);

      } else {
        throw new Error(result.details || "Calibration failed.");
      }
    } catch (error) {
      showAlert("danger", `<i class="fas fa-exclamation-triangle"></i> Calibration Error: ${error.message}`);
    } finally {
      // Reset button state
      calibrateBtn.innerHTML = '<i class="fas fa-sliders-h"></i> Calibrate Microphone';
      calibrateBtn.disabled = false;
    }
  }

  async function measureNoise() {
    console.log('Measure noise function called');
    try {
      // Update button state
      const originalText = measureNoiseBtn.innerHTML;
      measureNoiseBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Measuring...';
      measureNoiseBtn.disabled = true;

      showAlert(
        "info",
        "Measuring background noise... Please remain silent for a few seconds."
      );

      const response = await fetch("/calibrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "measure_noise" }),
      });

      const result = await response.json();

      if (result.status === "success") {
        const noise = result.noise_profile;
        const noiseHtml = `
          <div class="noise-results">
            <h6><i class="fas fa-volume-down text-success"></i> Background Noise Profile Captured!</h6>
            <div class="row mt-3">
              <div class="col-md-3">
                <div class="metric-card">
                  <div class="metric-label">RMS Level</div>
                  <div class="metric-value">${noise.rms.toFixed(4)}</div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="metric-card">
                  <div class="metric-label">Peak Level</div>
                  <div class="metric-value">${noise.peak.toFixed(4)}</div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="metric-card">
                  <div class="metric-label">Mean</div>
                  <div class="metric-value">${noise.mean.toFixed(6)}</div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="metric-card">
                  <div class="metric-label">Std Dev</div>
                  <div class="metric-value">${noise.std.toFixed(6)}</div>
                </div>
              </div>
            </div>
            <div class="mt-2">
              <small class="text-muted">
                <i class="fas fa-info-circle"></i> Background noise profile will be used to improve speech recognition accuracy
              </small>
            </div>
          </div>
        `;

        showAlert("success", noiseHtml);

        // Update noise status in the card
        updateCalibrationStatus('noise_measured', noise);

      } else {
        throw new Error(result.details || "Noise measurement failed.");
      }
    } catch (error) {
      showAlert("danger", `<i class="fas fa-exclamation-triangle"></i> Noise Measurement Error: ${error.message}`);
    } finally {
      // Reset button state
      measureNoiseBtn.innerHTML = '<i class="fas fa-volume-down"></i> Measure Background Noise';
      measureNoiseBtn.disabled = false;
    }
  }

  function updateCalibrationStatus(type, data) {
    const statusArea = document.getElementById("calibrationStatus");
    if (!statusArea) return;

    if (type === 'calibrated') {
      statusArea.innerHTML = `
        <div class="alert alert-success">
          <i class="fas fa-check-circle"></i> Microphone calibrated successfully
          <small class="d-block">Gain: ${data.gain.toFixed(2)} | Threshold: ${data.noise_threshold.toFixed(4)}</small>
        </div>
      `;
    } else if (type === 'noise_measured') {
      statusArea.innerHTML = `
        <div class="alert alert-info">
          <i class="fas fa-volume-down"></i> Background noise profile captured
          <small class="d-block">RMS: ${data.rms.toFixed(4)} | Peak: ${data.peak.toFixed(4)}</small>
        </div>
      `;
    }
  }

  function updateTranscriptionStatus(status, message) {
    const indicator = document.getElementById("transcriptionStatusIndicator");
    const statusText = document.getElementById("transcriptionStatusText");

    if (!indicator || !statusText) return;

    // Remove all status classes
    indicator.classList.remove('status-ready', 'status-pending', 'status-error');

    switch(status) {
      case 'ready':
        indicator.classList.add('status-ready');
        statusText.textContent = message || 'Ready to transcribe';
        break;
      case 'recording':
        indicator.classList.add('status-pending');
        statusText.textContent = message || 'Recording...';
        break;
      case 'processing':
        indicator.classList.add('status-pending');
        statusText.textContent = message || 'Processing...';
        break;
      case 'completed':
        indicator.classList.add('status-ready');
        statusText.textContent = message || 'Transcription complete';
        break;
      case 'error':
        indicator.classList.add('status-error');
        statusText.textContent = message || 'Error occurred';
        break;
    }
  }

  function showAlert(type, message) {
    // Clear all existing alerts to show only one at a time
    const existingAlerts = alertArea.querySelectorAll('.alert');
    existingAlerts.forEach(alert => {
      alert.parentElement.remove();
    });

    const wrapper = document.createElement("div");
    wrapper.innerHTML = [
      `<div class="alert alert-${type} alert-dismissible" role="alert">`,
      `   <div>${message}</div>`,
      '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
      "</div>",
    ].join("");
    alertArea.append(wrapper);

    // Auto-dismiss audio quality warnings after 5 seconds
    if (message.includes('Audio Quality:')) {
      setTimeout(() => {
        if (wrapper.parentNode) {
          wrapper.remove();
        }
      }, 5000);
    }
  }

  function startVisualization(audioStream) {
    if (!audioContext) {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (!analyser) {
      analyser = audioContext.createAnalyser();
    }

    const source = audioContext.createMediaStreamSource(audioStream);
    source.connect(analyser);

    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const canvas = audioVisualizer;
    const canvasCtx = canvas.getContext("2d");
    canvas.style.display = "block";

    let audioQualityCheckCount = 0;
    let lowVolumeWarningShown = false;

    function draw() {
      visualizationId = requestAnimationFrame(draw);

      analyser.getByteFrequencyData(dataArray);

      // Audio quality monitoring
      audioQualityCheckCount++;
      if (audioQualityCheckCount % 60 === 0) { // Check every ~1 second
        const averageVolume = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;

        if (averageVolume < 10 && !lowVolumeWarningShown) {
          showAlert('warning', '<i class="fas fa-volume-down"></i> Low audio input detected. Please speak louder or check your microphone.');
          lowVolumeWarningShown = true;
          setTimeout(() => { lowVolumeWarningShown = false; }, 10000); // Reset warning after 10 seconds
        }
      }

      canvasCtx.fillStyle = "#f8f9fa"; // Light background
      canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2.5;
      let barHeight;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        barHeight = dataArray[i] / 2;

        // Color bars based on volume level for visual feedback
        if (barHeight < 20) {
          canvasCtx.fillStyle = `rgb(200, 50, 50)`; // Red for low volume
        } else if (barHeight < 60) {
          canvasCtx.fillStyle = `rgb(200, 200, 50)`; // Yellow for medium volume
        } else {
          canvasCtx.fillStyle = `rgb(50, 200, 50)`; // Green for good volume
        }

        canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 1;
      }
    }
    draw();
  }

  function stopVisualization() {
    if (visualizationId) {
      cancelAnimationFrame(visualizationId);
    }
    if (audioVisualizer.getContext("2d")) {
      audioVisualizer
        .getContext("2d")
        .clearRect(0, 0, audioVisualizer.width, audioVisualizer.height);
    }
    audioVisualizer.style.display = "none";
    visualizationId = null;
  }

  async function uploadRecording() {
    if (recordedChunks.length === 0) {
      console.warn("No data recorded.");
      recordingStatus.innerHTML = "";
      return;
    }

    const blob = new Blob(recordedChunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("audio", blob, "recording.webm");

    try {
      const response = await fetch("/upload_audio", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }

      const result = await response.json();

      if (result.status === "success") {
        // Set the complete transcript and update the result
        completeFinalTranscript = result.text;
        updateTranscriptionResult();

        if (editor) {
          editor.innerHTML = result.text; // Also populate the editor
        }

        updateTranscriptionStatus('completed', 'Transcription completed successfully');
        showAlert("success", "<i class='fas fa-check-circle'></i> Transcription completed successfully!");

        if (transcriptionEditorTab) {
          transcriptionEditorTab.show(); // Switch to editor tab
        }
      } else {
        throw new Error(result.error || "Transcription failed on the server.");
      }
    } catch (error) {
      console.error("Error uploading recording:", error);
      updateTranscriptionStatus('error', 'Transcription failed');
      showAlert("danger", `<i class='fas fa-exclamation-triangle'></i> An error occurred: ${error.message}`);
    } finally {
      recordingStatus.innerHTML = "";
      recordedChunks = [];
    }
  }

});
