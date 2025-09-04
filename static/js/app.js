console.log('JavaScript file loaded - CLEAN VERSION');

document.addEventListener("DOMContentLoaded", function () {
  console.log('DOM Content Loaded - CLEAN VERSION');

  // Test to see if JavaScript is working
  setTimeout(() => {
    console.log('Testing JavaScript execution...');

    // Test button clicks
    const calibrateBtn = document.getElementById("calibrateBtn");
    const measureNoiseBtn = document.getElementById("measureNoiseBtn");
    const recordButton = document.getElementById("recordButton");

    console.log('Button elements found:', {
      calibrateBtn: !!calibrateBtn,
      measureNoiseBtn: !!measureNoiseBtn,
      recordButton: !!recordButton
    });

    if (calibrateBtn) {
      calibrateBtn.addEventListener("click", function() {
        console.log('Calibrate button clicked!');
        alert('Calibrate button works!');
      });
    }

    if (measureNoiseBtn) {
      measureNoiseBtn.addEventListener("click", function() {
        console.log('Measure noise button clicked!');
        alert('Measure noise button works!');
      });
    }

    if (recordButton) {
      recordButton.addEventListener("click", function() {
        console.log('Record button clicked!');
        alert('Record button works!');
      });
    }
  }, 1000);

});
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

    // Initialize Socket.IO
    try {
      initializeSocket();
    } catch (error) {
      console.error('Socket.IO initialization failed:', error);
    }

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
    if (streamingMode) {
      streamingMode.addEventListener("change", handleModeChange);
      console.log('Streaming mode listener added');
    }

    // Initialize UI
    updateTranscriptionStatus('ready', 'Ready to transcribe');
    handleModeChange(); // Set initial mode
    console.log('App initialization complete');
  }

  function initializeSocket() {
    console.log('Initializing Socket.IO...');
    if (typeof io === 'undefined') {
      console.error('Socket.IO library not loaded');
      return;
    }
    socket = io();

    socket.on('connect', function() {
      console.log('Connected to server');
    });

    socket.on('disconnect', function() {
      console.log('Disconnected from server');
      if (isRecording && isStreamingMode) {
        stopRecording();
      }
    });

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
    });

    socket.on('streaming_error', function(data) {
      console.error('Streaming error:', data);
      showAlert('danger', `<i class='fas fa-exclamation-triangle'></i> Streaming Error: ${data.message}`);
      if (isRecording) {
        stopRecording();
      }
    });
  }

  function handleModeChange() {
    isStreamingMode = streamingMode.checked;

    if (isStreamingMode) {
      recordButtonText.textContent = "Start Live Transcription";
      modeDescription.textContent = "Live transcription with instant results";
      streamingTranscription.style.display = "block";
      transcriptionResult.style.display = "none";
    } else {
      recordButtonText.textContent = "Start Recording";
      modeDescription.textContent = "Record first, then transcribe";
      streamingTranscription.style.display = "none";
      transcriptionResult.style.display = "block";
    }
  }

  function toggleRecording() {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }

  function handleTranscriptionChunk(data) {
    if (data.text && data.text.trim()) {
      const confidence = data.confidence || 0.5;
      const confidenceClass = confidence > 0.8 ? 'high' : confidence > 0.5 ? 'medium' : 'low';

      // Create chunk element
      const chunkElement = document.createElement('span');
      chunkElement.className = `transcript-chunk confidence-${confidenceClass}`;
      chunkElement.innerHTML = `${data.text} <span class="confidence-indicator confidence-${confidenceClass}"></span>`;

      // Add to live transcript
      const existingContent = liveTranscriptText.innerHTML;
      if (existingContent.includes('Listening for speech')) {
        liveTranscriptText.innerHTML = '';
      }

      liveTranscriptText.appendChild(chunkElement);
      liveTranscriptText.appendChild(document.createTextNode(' '));

      // Auto-scroll to bottom
      liveTranscriptText.scrollTop = liveTranscriptText.scrollHeight;

      // Store chunk
      transcriptChunks.push({
        text: data.text,
        confidence: confidence,
        timestamp: Date.now(),
        chunk_id: data.chunk_id
      });

      // Update stats
      updateStreamingStats();
    }
  }

  function updateStreamingStats() {
    const totalChunks = transcriptChunks.length;
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

  async function startRecording() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      });

      isRecording = true;
      recordedChunks = [];
      transcriptChunks = [];

      if (isStreamingMode) {
        startStreamingTranscription();
      } else {
        startTraditionalRecording();
      }

      recordButton.innerHTML = "<i class='fas fa-stop'></i> Stop Recording";
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
            <div class="small">Speak clearly into your microphone</div>
          </div>
        </div>
      `;

      updateTranscriptionStatus('recording', `${modeText}...`);
      startVisualization(stream);

    } catch (err) {
      console.error("Error starting recording:", err);
      updateTranscriptionStatus('error', 'Microphone access denied');
      showAlert(
        "danger",
        "<i class='fas fa-exclamation-triangle'></i> Could not start recording. Please ensure you have given microphone permissions."
      );
    }
  }

  function startStreamingTranscription() {
    // Start streaming session
    socket.emit('start_streaming', {
      use_calibration: true, // You can make this configurable
      use_phrases: true
    });

    // Set up MediaRecorder for streaming
    mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus',
      audioBitsPerSecond: 16000
    });

    mediaRecorder.ondataavailable = function (e) {
      if (e.data.size > 0 && streamingSessionId) {
        // Convert blob to base64 and send to server
        const reader = new FileReader();
        reader.onload = function() {
          const base64Audio = reader.result.split(',')[1];
          socket.emit('audio_chunk', {
            session_id: streamingSessionId,
            audio_data: base64Audio,
            chunk_id: audioChunkCounter++
          });
        };
        reader.readAsDataURL(e.data);
      }
    };

    // Start recording in small chunks (500ms)
    mediaRecorder.start(500);

    // Clear live transcript
    liveTranscriptText.innerHTML = `
      <div class="text-center text-muted">
        <i class="fas fa-microphone fa-2x mb-3"></i>
        <p class="mb-0">Listening for speech...</p>
        <small>Start speaking to see real-time transcription</small>
      </div>
    `;
  }

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

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
    }

    isRecording = false;

    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }

    stopVisualization();

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
        // Update transcription result with better formatting
        transcriptionResult.innerHTML = `
          <div class="transcription-content">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h6 class="mb-0"><i class="fas fa-check-circle text-success"></i> Transcription Complete</h6>
              <small class="text-muted">Confidence: ${(result.confidence * 100 || 85).toFixed(1)}%</small>
            </div>
            <div class="transcribed-text p-3 bg-white border rounded">
              ${result.text}
            </div>
          </div>
        `;

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

    function draw() {
      visualizationId = requestAnimationFrame(draw);

      analyser.getByteFrequencyData(dataArray);

      canvasCtx.fillStyle = "#f8f9fa"; // Light background
      canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2.5;
      let barHeight;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        barHeight = dataArray[i] / 2;
        canvasCtx.fillStyle = `rgb(50, 50, ${barHeight + 100})`;
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
    // Do not close audioContext here to avoid issues on multiple recordings
  }

  function showAlert(type, message) {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = [
      `<div class="alert alert-${type} alert-dismissible" role="alert">`,
      `   <div>${message}</div>`,
      '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
      "</div>",
    ].join("");
    alertArea.append(wrapper);
  }

  async function calibrateMicrophone() {
    console.log('Calibrate microphone function called');
    try {
      // Update button state
      const calibrateBtn = document.getElementById("calibrateBtn");
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
      const calibrateBtn = document.getElementById("calibrateBtn");
      calibrateBtn.innerHTML = '<i class="fas fa-sliders-h"></i> Calibrate Microphone';
      calibrateBtn.disabled = false;
    }
  }

  async function measureNoise() {
    console.log('Measure noise function called');
    try {
      // Update button state
      const measureBtn = document.getElementById("measureNoiseBtn");
      const originalText = measureBtn.innerHTML;
      measureBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Measuring...';
      measureBtn.disabled = true;

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
      const measureBtn = document.getElementById("measureNoiseBtn");
      measureBtn.innerHTML = '<i class="fas fa-volume-up"></i> Measure Background Noise';
      measureBtn.disabled = false;
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
});
