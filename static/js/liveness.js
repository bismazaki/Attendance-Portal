const video = document.getElementById('regVideo');
const canvas = document.getElementById('regCanvas');
const previewContainer = document.getElementById('previewContainer');
let capturedImages = [];
let blinkCount = 0;
let headLeft = false;
let headRight = false;
let captured = false;

// Load models from /static/models
Promise.all([
  faceapi.nets.tinyFaceDetector.loadFromUri('/static/models'),
  faceapi.nets.faceLandmark68TinyNet.loadFromUri('/static/models')
]).then(startVideo);

// Start webcam
function startVideo() {
  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => video.srcObject = stream)
    .catch(err => console.error("Camera error:", err));
}

// Calculate Eye Aspect Ratio for blink detection
function getEAR(eye) {
  const a = faceapi.euclideanDistance(eye[1], eye[5]);
  const b = faceapi.euclideanDistance(eye[2], eye[4]);
  const c = faceapi.euclideanDistance(eye[0], eye[3]);
  return (a + b) / (2.0 * c);
}

// Run liveness detection
video.addEventListener('play', () => {
  const displaySize = { width: video.width, height: video.height };
  const interval = setInterval(async () => {
    const detection = await faceapi.detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
      .withFaceLandmarks(true);
    
    if (detection) {
      const resized = faceapi.resizeResults(detection, displaySize);

      // Blink detection
      const leftEye = resized.landmarks.getLeftEye();
      const rightEye = resized.landmarks.getRightEye();
      const leftEAR = getEAR(leftEye);
      const rightEAR = getEAR(rightEye);
      if (leftEAR < 0.25 && rightEAR < 0.25) blinkCount++;

      // Head movement detection (nose X position)
      const nose = resized.landmarks.getNose();
      const noseX = nose[3].x;
      if (noseX < video.width * 0.4) headLeft = true;
      if (noseX > video.width * 0.6) headRight = true;

      // Liveness passed: capture once
      if (blinkCount >= 2 && headLeft && headRight && !captured) {
        captured = true;
        captureFace();
        clearInterval(interval);
      }
    }
  }, 200);
});

// Capture face image
function captureFace() {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
  const dataURL = canvas.toDataURL("image/png");
  capturedImages.push(dataURL);

  const img = document.createElement("img");
  img.src = dataURL;
  img.classList.add("preview-img");
  previewContainer.appendChild(img);

  document.getElementById('statusMsg').innerText = `✅ Liveness verified and face captured!`;
}

// Submit registration form
document.getElementById("registerForm").addEventListener("submit", async function(e){
  e.preventDefault();
  let name = document.getElementById("fullName").value.trim();
  let email = document.getElementById("email").value.trim();
  let password = document.getElementById("password").value.trim();

  if (!name || !email || !password) {
    document.getElementById("statusMsg").innerText = "❌ All fields are required!";
    return;
  }
  if (capturedImages.length === 0) {
    document.getElementById("statusMsg").innerText = "❌ Liveness not verified yet!";
    return;
  }

  let response = await fetch("/api/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: name,
      email: email,
      password: password,
      face_images: capturedImages
    })
  });

  let result = await response.json();
  document.getElementById("statusMsg").innerText = result.message;

  if (result.success) {
    alert(`🎉 Registered Successfully!\nYour Student-ID: ${result.student_id}`);
    window.location.href = "/login";
  }
});
