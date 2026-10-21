// Voice recording + transcription for Treatment Companion.

(function () {
  const micBtn = document.getElementById("micBtn");
  if (!micBtn) return;

  const voiceTitle = document.getElementById("voiceTitle");
  const voiceHint = document.getElementById("voiceHint");
  const indicator = document.getElementById("recordingIndicator");
  const errorEl = document.getElementById("voiceError");
  const textarea = document.getElementById("raw_text");

  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;
  let stream = null;

  function setError(msg) {
    if (errorEl) {
      errorEl.textContent = msg;
      errorEl.style.display = msg ? "block" : "none";
    }
  }

  function setStatus(title, hint) {
    if (voiceTitle) voiceTitle.textContent = title;
    if (voiceHint) voiceHint.textContent = hint;
  }

  async function startRecording() {
    setError("");
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      setError("Microphone access denied. Please allow the mic and try again.");
      return;
    }

    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());

      const blob = new Blob(audioChunks, { type: "audio/webm" });
      if (blob.size < 1000) {
        setError("Recording was too short. Try again.");
        resetUI();
        return;
      }

      setStatus("Transcribing...", "Sending your voice to the AI.");
      try {
        const formData = new FormData();
        formData.append("audio", blob, "recording.webm");

        const resp = await fetch("/api/transcribe", {
          method: "POST",
          body: formData,
        });

        const data = await resp.json();

        if (!resp.ok || data.error) {
          throw new Error(data.error || "Transcription failed");
        }

        if (textarea) {
          textarea.value = data.text;
          textarea.focus();
        }
        setStatus("Done! Review and edit below.", "Tap the mic again to record another.");
      } catch (e) {
        setError("Transcription error: " + e.message);
        setStatus("Tap to speak", "Try again or type it instead.");
      } finally {
        resetUI();
      }
    };

    mediaRecorder.start();
    isRecording = true;
    micBtn.classList.add("recording");
    micBtn.querySelector(".mic-icon").textContent = "⏹";
    if (indicator) indicator.style.display = "flex";
    setStatus("Listening...", "Speak clearly. Tap the mic again to stop.");
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    isRecording = false;
    if (indicator) indicator.style.display = "none";
    micBtn.classList.remove("recording");
    micBtn.querySelector(".mic-icon").textContent = "🎤";
  }

  function resetUI() {
    isRecording = false;
    if (indicator) indicator.style.display = "none";
    micBtn.classList.remove("recording");
    const icon = micBtn.querySelector(".mic-icon");
    if (icon) icon.textContent = "🎤";
  }

  micBtn.addEventListener("click", () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  });

  window.addEventListener("beforeunload", () => {
    if (stream) stream.getTracks().forEach((t) => t.stop());
  });
})();