const facemanagerStatus = document.getElementById("facemanager-status");
const databasemanagerStatus = document.getElementById("databasemanager-status");
const startBtn = document.getElementById("start-btn");
const videoBtn = document.getElementById("video-btn");
const resolutionSelect = document.getElementById("resolution-select");
const detectCheckbox = document.getElementById("detect");
const identifyCheckbox = document.getElementById("identify");
const toggleOptionsBtn = document.getElementById("toggle-options");
const optionsDropdown = document.getElementById("options-dropdown");
const framerateSlider = document.getElementById("framerate-slider");
const framerateValue = document.getElementById("framerate-value");
const canvas = document.getElementById("videoCanvas");
const ctx = canvas.getContext("2d");

let currentSocket = null;
let currentStreamType = null; // "detect" or "video"

// Toggle dropdown options visibility
toggleOptionsBtn.addEventListener("click", () => {
    optionsDropdown.classList.toggle("hidden");
    toggleOptionsBtn.textContent = optionsDropdown.classList.contains("hidden") ? "Options ▼" : "Options ▲";
});

// Load available resolutions and framerate limit
async function loadResolutions() {
    try {
        const res = await fetch("/supported");
        const data = await res.json();

        data.resolutions.forEach(({ width, height }) => {
            const option = document.createElement("option");
            option.value = `${width}x${height}`;
            option.textContent = `${width} x ${height}`;
            resolutionSelect.appendChild(option);
        });

        framerateSlider.max = data.framerate;
        framerateSlider.min = 1;
        framerateSlider.value = data.framerate;
        framerateValue.textContent = data.framerate;
    } catch (err) {
        console.error("Error loading resolutions or framerate:", err);
    }
}

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

// Start/Stop detection stream
startBtn.addEventListener('click', () => {
    if (currentStreamType === "detect") {
        closeCurrentStream();
    } else {
        closeCurrentStream();
        const detect = detectCheckbox.checked;
        const identify = identifyCheckbox.checked;
        const [width, height] = resolutionSelect.value.split('x');
        const fps = framerateSlider.value;
        const url = `ws://localhost:9253/ws/video_feed?detect=${detect}&identify=${identify}&width=${width}&height=${height}&fps_target=${fps}`;
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
        const [width, height] = resolutionSelect.value.split('x');
        const fps = framerateSlider.value;
        const url = `ws://localhost:9253/ws/video_feed?detect=false&identify=false&width=${width}&height=${height}&fps_target=${fps}`;
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
        currentStreamType = "video";
        videoBtn.textContent = "Stop Video";
    }
});

// Handle resolution change
resolutionSelect.addEventListener("change", async () => {
    if (currentStreamType) {
        closeCurrentStream();
        await new Promise(resolve => setTimeout(resolve, 300));
        if (currentStreamType === "detect") {
            startBtn.click();
        } else if (currentStreamType === "video") {
            videoBtn.click();
        }
    }
});

// Handle framerate change
framerateSlider.addEventListener("mouseup", async () => {
    if (currentStreamType) {
        closeCurrentStream();
        await new Promise(resolve => setTimeout(resolve, 300));
        if (currentStreamType === "detect") {
            startBtn.click();
        } else if (currentStreamType === "video") {
            videoBtn.click();
        }
    }
});

// Update framerate value display
framerateSlider.addEventListener("input", () => {
    framerateValue.textContent = framerateSlider.value;
});

async function init() {
    await loadResolutions();
    optionsDropdown.classList.add("hidden");
    toggleOptionsBtn.textContent = "Options ▼";
}

window.onload = init;