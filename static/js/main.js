const facemanagerStatus = document.getElementById("facemanager-status");
const databasemanagerStatus = document.getElementById("databasemanager-status");
const startBtn = document.getElementById("start-btn");
const videoBtn = document.getElementById("video-btn");
const resolutionSelect = document.getElementById("resolution-select");
const toggleOptionsBtn = document.getElementById("toggle-options");
const optionsDropdown = document.getElementById("options-dropdown");
const framerateSlider = document.getElementById("framerate-slider");
const contrastSlider = document.getElementById("contrast-slider");
const gammaSlider = document.getElementById("gamma-slider")
const framerateValue = document.getElementById("framerate-value");
const canvas = document.getElementById("videoCanvas");
const ctx = canvas.getContext("2d");

let currentSocket = null;
let currentStreamType = null; // "detect" or "video"

import {facemanagerConnected, connectFaceManager} from './connection.js'

// Toggle dropdown options visibility
toggleOptionsBtn.addEventListener("click", () => {
    optionsDropdown.classList.toggle("hidden");
    toggleOptionsBtn.textContent = optionsDropdown.classList.contains("hidden") ? "Options ▼" : "Options ▲";
});


// Close the current WebSocket stream if active
function closeCurrentStream() {
    if (currentSocket) {
        currentSocket.close();
        currentSocket = null;
        currentStreamType = null;
        startBtn.textContent = "Start";
        videoBtn.textContent = "Video Feed";
    }
}

function startStream(should_detect=null, should_identify=null){
    const detect = should_detect===null?true:should_detect;
    const identify = should_identify===null?true:should_identify; 
    const [width, height] = resolutionSelect.value.split('x');
    const fps = framerateSlider.value;
    const contrast = contrastSlider.value;
    const gamma = gammaSlider.value;
    const url = `ws://localhost:9253/ws/video_feed?detect=${detect}&identify=${identify}&width=${width}&height=${height}&fps_target=${fps}&gamma=${gamma}&contrast=${contrast}`;
    canvas.width = parseInt(width);
    canvas.height = parseInt(height);
    currentSocket = new WebSocket(url);
    currentSocket.binaryType = "arraybuffer";
    currentSocket.onmessage = (event) => {
        const blob = new Blob([event.data], { type: 'image/jpeg' });
        const url = URL.createObjectURL(blob);
        const img = new Image();
        img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            URL.revokeObjectURL(url);
        };
        img.src = url;
    };
}

// Start/Stop detection stream
startBtn.addEventListener('click', async () => {
    if (!facemanagerConnected){
        startBtn.setAttribute("disabled", true);
        await connectFaceManager();
        startBtn.removeAttribute("disabled");
    }
    if (currentStreamType === "detect") {
        closeCurrentStream();
    } else {
        closeCurrentStream();
        startStream();
        currentStreamType = "detect";
        startBtn.textContent = "Stop";
    }
});

// Start/Stop raw video feed
videoBtn.addEventListener('click', () => {
    if (currentStreamType === "video") {
        closeCurrentStream();
    } else {
        closeCurrentStream();
        startStream(false, false);
        currentStreamType = "video";
        videoBtn.textContent = "Stop Video";
    }
});

// Handle resolution change
resolutionSelect.addEventListener("change", restartVideo);
// Handle framerate change
framerateSlider.addEventListener("mouseup", restartVideo);
// Handle contrast change
contrastSlider.addEventListener("mouseup", restartVideo);
// Handle gamma change
gammaSlider.addEventListener("mouseup", restartVideo);

async function restartVideo() {
    const laststreamtype = currentStreamType;
    closeCurrentStream()
    if (laststreamtype === "detect") {
        startStream();
        currentStreamType = "detect";
        startBtn.textContent = "Stop";
    } else if (laststreamtype === "video") {
        startStream(false, false);
        currentStreamType = "video";
        videoBtn.textContent = "Stop Video";
    }
}

// Update framerate value display
framerateSlider.addEventListener("input", () => {
    framerateValue.textContent = framerateSlider.value;
});