document.addEventListener("DOMContentLoaded", function () {
  // This code is moved from templates/index.html

  // Global variables
  let mediaRecorder = null;
  let chunks = [];
  let isRecording = false;
  let stream = null;
  let visualizationInterval = null;
  let audioContext = null;
  let analyser = null;
  let canvasCtx = null;
  let socket = null;

  // Get DOM elements
  const recordButton = document.getElementById("recordButton");
  const recordingStatus = document.getElementById("recordingStatus");
  const transcriptionResult = document.getElementById("transcriptionResult");
  const alertArea = document.getElementById("alertArea");
  const audioVisualizer = document.getElementById("audioVisualizer");

  // Initialize the application
  function initializeApp() {
    console.log("Setting up application...");

    if (!hasGetUserMedia()) {
      console.error("getUserMedia not supported");
      showAlert("error", "Your browser does not support audio recording.");
      recordButton.disabled = true;
      return;
    }

    // Add click event listener for the record button
    if (recordButton) {
      recordButton.addEventListener("click", handleRecordButtonClick);
      console.log("Record button event listener added.");
    }

    // Test microphone access
    testMicrophoneAccess();

    // Add calibration button event listeners
    const calibrateBtn = document.getElementById("calibrateBtn");
    const measureNoiseBtn = document.getElementById("measureNoiseBtn");

    if (calibrateBtn) {
      calibrateBtn.addEventListener("click", calibrateMicrophone);
    }

    if (measureNoiseBtn) {
      measureNoiseBtn.addEventListener("click", measureNoise);
    }

    // Phrase Dictionary Management
    const addPhraseForm = document.getElementById("addPhraseForm");
    if (addPhraseForm) {
      addPhraseForm.addEventListener("submit", addPhrase);
      loadPhrases();
    }
  }

  // Calibration functions
  async function calibrateMicrophone() {
    try {
      showAlert("info", "Starting microphone calibration...");
      const response = await fetch("/calibrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "calibrate" }),
      });

      const result = await response.json();
      if (result.status === "success") {
        showAlert("success", "Calibration completed successfully!");
        const calibrationInfo = `
                    <div class="alert alert-info">
                      <h5>Calibration Results:</h5>
                      <p>Gain: ${result.calibration.gain.toFixed(2)}</p>
                      <p>Noise Threshold: ${result.calibration.noise_threshold.toFixed(
                        4
                      )}</p>
                    </div>
                  `;
        recordingStatus.innerHTML = calibrationInfo;
      } else {
        throw new Error(result.error || "Calibration failed");
      }
    } catch (error) {
      console.error("Calibration error:", error);
      showAlert("error", "Failed to calibrate microphone: " + error.message);
    }
  }

  async function measureNoise() {
    try {
      showAlert("info", "Measuring background noise...");
      const response = await fetch("/calibrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "measure_noise" }),
      });

      const result = await response.json();
      if (result.status === "success") {
        showAlert("success", "Noise measurement completed!");
        const noiseInfo = `
                    <div class="alert alert-info">
                      <h5>Noise Measurement:</h5>
                      <p>Average Level: ${result.noise_profile.mean.toFixed(
                        4
                      )}</p>
                      <p>Peak Level: ${result.noise_profile.peak.toFixed(4)}</p>
                    </div>
                  `;
        recordingStatus.innerHTML = noiseInfo;
      } else {
        throw new Error(result.error || "Noise measurement failed");
      }
    } catch (error) {
      console.error("Noise measurement error:", error);
      showAlert("error", "Failed to measure noise: " + error.message);
    }
  }

  // Check if browser supports getUserMedia
  function hasGetUserMedia() {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  }

  async function testMicrophoneAccess() {
    try {
      // Just request access to test if it works
      const testStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      console.log("Microphone access test successful");
      // Stop all tracks immediately
      testStream.getTracks().forEach((track) => track.stop());
    } catch (error) {
      console.error("Microphone access test failed:", error);
      showAlert(
        "error",
        "Please allow microphone access to use this application."
      );
    }
  }

  async function handleRecordButtonClick() {
    console.log("Record button clicked, current state:", isRecording);
    if (!isRecording) {
      await startRecording();
    } else {
      await stopRecording();
    }
  }

  async function startRecording() {
    try {
      console.log("Requesting microphone permission...");
      showAlert("info", "Requesting microphone access...");

      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }

      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      console.log("Microphone permission granted!");
      showAlert("success", "Microphone access granted! Starting recording...");

      // Connect to WebSocket server
      socket = io.connect("http://" + document.domain + ":" + location.port);

      socket.on("connect", function () {
        console.log("WebSocket connected!");
        transcriptionResult.innerHTML = ""; // Clear previous transcription
      });

      socket.on("disconnect", function () {
        console.log("WebSocket disconnected.");
      });

      socket.on("response", function (msg) {
        if (msg.status === "success" && msg.text) {
          transcriptionResult.innerHTML += msg.text + " ";
        } else if (msg.status === "error") {
          console.error("Server error:", msg.message);
        }
      });

      // Change button state
      recordButton.innerHTML = "<i class='fas fa-stop'></i> Stop Recording";
      recordButton.classList.remove("btn-primary");
      recordButton.classList.add("btn-danger");

      // Start recording
      mediaRecorder = new MediaRecorder(stream);
      chunks = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          socket.emit("audio_chunk", e.data);
        }
      };

      mediaRecorder.onstart = () => {
        console.log("Recording started");
        isRecording = true;
        recordingStatus.innerHTML =
          "<div class='alert alert-info'>" +
          "<i class='fas fa-microphone'></i> Recording in progress..." +
          "<div class='progress mt-2'>" +
          "<div class='progress-bar progress-bar-striped progress-bar-animated' " +
          "role='progressbar' style='width: 100%'></div>" +
          "</div></div>";

        startVisualization(stream);
      };

      mediaRecorder.onstop = async () => {
        console.log("Recording stopped");
        isRecording = false;

        if (socket) {
          socket.disconnect();
        }

        // Reset recording status
        recordingStatus.innerHTML = "";

        // Stop visualization
        stopVisualization();
      };

      // Start recording with 1 second timeslices
      mediaRecorder.start(1000);
      console.log("MediaRecorder started");
    } catch (error) {
      console.error("Recording error:", error);
      showAlert("error", "Failed to start recording: " + error.message);
      if (error.name === "NotAllowedError") {
        showAlert(
          "error",
          "Microphone permission denied. Please allow microphone access and try again."
        );
      } else if (error.name === "NotFoundError") {
        showAlert(
          "error",
          "No microphone found. Please connect a microphone and try again."
        );
      }

      // Reset button state
      recordButton.innerHTML =
        "<i class='fas fa-microphone'></i> Start Recording";
      recordButton.classList.remove("btn-danger");
      recordButton.classList.add("btn-primary");
    }
  }

  async function stopRecording() {
    console.log("Stopping recording...");
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();

      // Reset button
      recordButton.innerHTML =
        "<i class='fas fa-microphone'></i> Start Recording";
      recordButton.classList.remove("btn-danger");
      recordButton.classList.add("btn-primary");

      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
        stream = null;
      }
      if (socket) {
        socket.disconnect();
      }
    }
  }

  function showAlert(type, message) {
    console.log("Alert:", type, message);
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      `;

    // Remove any existing alerts
    const existingAlerts = document.querySelectorAll(".alert");
    existingAlerts.forEach((alert) => alert.remove());

    // Add the new alert
    alertArea.appendChild(alertDiv);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      if (alertDiv.parentNode === alertArea) {
        alertArea.removeChild(alertDiv);
      }
    }, 5000);
  }

  function startVisualization(stream) {
    try {
      canvasCtx = audioVisualizer.getContext("2d");

      // Create audio context
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      analyser = audioContext.createAnalyser();

      // Connect the stream
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);

      // Configure analyser
      analyser.fftSize = 2048;
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      // Draw function
      function draw() {
        if (!isRecording) return;

        requestAnimationFrame(draw);
        analyser.getByteTimeDomainData(dataArray);

        canvasCtx.fillStyle = "rgb(200, 200, 200)";
        canvasCtx.fillRect(0, 0, audioVisualizer.width, audioVisualizer.height);

        canvasCtx.lineWidth = 2;
        canvasCtx.strokeStyle = "rgb(0, 123, 255)";
        canvasCtx.beginPath();

        const sliceWidth = (audioVisualizer.width * 1.0) / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
          const v = dataArray[i] / 128.0;
          const y = (v * audioVisualizer.height) / 2;

          if (i === 0) {
            canvasCtx.moveTo(x, y);
          } else {
            canvasCtx.lineTo(x, y);
          }

          x += sliceWidth;
        }

        canvasCtx.lineTo(audioVisualizer.width, audioVisualizer.height / 2);
        canvasCtx.stroke();
      }

      draw();
    } catch (error) {
      console.error("Visualization error:", error);
    }
  }

  function stopVisualization() {
    if (audioContext) {
      audioContext.close();
    }
  }

  // Phrase Dictionary Management
  async function loadPhrases() {
    const category = document.getElementById("filterCategory").value;
    const phraseList = document.getElementById("phraseList");

    try {
      const response = await fetch(`/phrases?category=${category}`);
      const data = await response.json();

      if (data.status === "success") {
        phraseList.innerHTML = data.phrases
          .map(
            (phrase) => `
            <div class="phrase-item">
              <span>${phrase}</span>
              <button class="btn btn-sm btn-danger" onclick="deletePhrase('${phrase}', '${category}')">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          `
          )
          .join("");
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      phraseList.innerHTML = `<div class="alert alert-danger">Error loading phrases: ${error.message}</div>`;
    }
  }

  async function addPhrase(event) {
    event.preventDefault();

    const phrase = document.getElementById("phraseText").value;
    const category = document.getElementById("phraseCategory").value;

    try {
      const response = await fetch("/phrases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phrase, category }),
      });

      const data = await response.json();

      if (data.status === "success") {
        document.getElementById("phraseText").value = "";
        loadPhrases();
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      alert(`Error adding phrase: ${error.message}`);
    }
  }

  async function deletePhrase(phrase, category) {
    if (!confirm(`Delete phrase "${phrase}"?`)) return;

    try {
      const response = await fetch("/phrases", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phrase, category }),
      });

      const data = await response.json();

      if (data.status === "success") {
        loadPhrases();
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      alert(`Error deleting phrase: ${error.message}`);
    }
  }

  // Editor Functions
  let currentTranscript = null;
  let speakers = new Set();
  let editHistory = [];
  let currentHistoryIndex = -1;

  function initializeEditor(transcriptData) {
    currentTranscript = transcriptData;
    const editor = document.getElementById("editor");

    // Clear existing content
    editor.innerHTML = "";

    // Format and display transcript
    let formattedText = "";
    transcriptData.segments.forEach((segment) => {
      const confidence = segment.confidence;
      const text = segment.text;

      // Add speaker if present
      if (segment.speaker) {
        speakers.add(segment.speaker);
        formattedText += `<div class="speaker-label">${segment.speaker}:</div>`;
      }

      // Add timestamp if present
      if (segment.timestamp) {
        formattedText += `<div class="timestamp">[${formatTime(
          segment.timestamp
        )}]</div>`;
      }

      // Add text with confidence highlighting
      formattedText += `<span class="segment" data-confidence="${confidence}">${text}</span>`;
    });

    editor.innerHTML = formattedText;
    updateConfidenceIndicators();
    updateSpeakersList();

    // Save initial state
    saveHistoryState();
  }

  function updateConfidenceIndicators() {
    const segments = document.querySelectorAll(".segment");
    let totalConfidence = 0;

    segments.forEach((segment) => {
      const confidence = parseFloat(segment.dataset.confidence);
      totalConfidence += confidence;

      if (confidence < 0.7) {
        segment.classList.add("low-confidence");
      }
    });

    const averageConfidence = totalConfidence / segments.length;
    const confidenceBar = document.getElementById("confidenceBar");
    confidenceBar.style.width = `${averageConfidence * 100}%`;
    confidenceBar.className = `progress-bar ${
      averageConfidence >= 0.8
        ? "bg-success"
        : averageConfidence >= 0.6
        ? "bg-warning"
        : "bg-danger"
    }`;
  }

  function updateSpeakersList() {
    const speakersList = document.getElementById("speakersList");
    speakersList.innerHTML = "";

    speakers.forEach((speaker) => {
      const speakerItem = document.createElement("div");
      speakerItem.className =
        "list-group-item d-flex justify-content-between align-items-center";
      speakerItem.innerHTML = `
          <span>${speaker}</span>
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-secondary" onclick="editSpeaker('${speaker}')">
              <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-outline-danger" onclick="deleteSpeaker('${speaker}')">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        `;
      speakersList.appendChild(speakerItem);
    });
  }

  function formatText(style) {
    document.execCommand(style, false, null);
  }

  function addSection(type) {
    const selection = window.getSelection();
    const range = selection.getRangeAt(0);
    const element = document.createElement("div");

    if (type === "speaker") {
      const speaker = prompt("Enter speaker name:");
      if (speaker) {
        element.className = "speaker-label";
        element.textContent = `${speaker}:`;
        speakers.add(speaker);
        updateSpeakersList();
      }
    } else if (type === "timestamp") {
      const timestamp = new Date().toISOString();
      element.className = "timestamp";
      element.textContent = `[${formatTime(timestamp)}]`;
    }

    range.insertNode(element);
    saveHistoryState();
  }

  function saveHistoryState() {
    const editor = document.getElementById("editor");
    const state = editor.innerHTML;

    // Remove future states if we're not at the latest point
    if (currentHistoryIndex < editHistory.length - 1) {
      editHistory = editHistory.slice(0, currentHistoryIndex + 1);
    }

    editHistory.push(state);
    currentHistoryIndex = editHistory.length - 1;

    // Limit history size
    if (editHistory.length > 50) {
      editHistory.shift();
      currentHistoryIndex--;
    }
  }

  function undo() {
    if (currentHistoryIndex > 0) {
      currentHistoryIndex--;
      const editor = document.getElementById("editor");
      editor.innerHTML = editHistory[currentHistoryIndex];
    }
  }

  function redo() {
    if (currentHistoryIndex < editHistory.length - 1) {
      currentHistoryIndex++;
      const editor = document.getElementById("editor");
      editor.innerHTML = editHistory[currentHistoryIndex];
    }
  }

  function saveTranscript() {
    const editor = document.getElementById("editor");
    const content = editor.innerHTML;

    // Save to server
    fetch("/save_transcript", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        content: content,
        speakers: Array.from(speakers),
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          showAlert("success", "Transcript saved successfully");
        } else {
          showAlert("error", "Error saving transcript");
        }
      })
      .catch((error) => {
        showAlert("error", "Error saving transcript");
        console.error("Error:", error);
      });
  }

  function showExportOptions() {
    const modal = new bootstrap.Modal(document.getElementById("exportModal"));
    modal.show();
  }

  function exportTranscript() {
    const format = document.getElementById("exportFormat").value;
    const includeTimestamps =
      document.getElementById("includeTimestamps").checked;
    const includeSpeakers = document.getElementById("includeSpeakers").checked;
    const includeConfidence =
      document.getElementById("includeConfidence").checked;

    const editor = document.getElementById("editor");
    const content = editor.innerHTML;

    fetch("/export_transcript", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        content: content,
        format: format,
        options: {
          includeTimestamps,
          includeSpeakers,
          includeConfidence,
        },
      }),
    })
      .then((response) => response.blob())
      .then((blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `transcript.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        const modal = bootstrap.Modal.getInstance(
          document.getElementById("exportModal")
        );
        modal.hide();
      })
      .catch((error) => {
        showAlert("error", "Error exporting transcript");
        console.error("Error:", error);
      });
  }

  function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  }

  // Initialize the application now that the DOM is ready
  initializeApp();
});
