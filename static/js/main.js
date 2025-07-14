// const facemanagerStatus = document.getElementById("facemanager-status");
// const databasemanagerStatus = document.getElementById("databasemanager-status");
// const startBtn = document.getElementById("start-btn");
// const videoBtn = document.getElementById("video-btn");
// const resolutionSelect = document.getElementById("resolution-select");
// const video = document.getElementById("video");

// const detectCheckbox = document.getElementById("detect");
// const identifyCheckbox = document.getElementById("identify");

// const toggleOptionsBtn = document.getElementById("toggle-options");
// const optionsDropdown = document.getElementById("options-dropdown");

// let facemanagerConnected = false;
// let databasemanagerConnected = false;
// let streaming = false;
// let lastUsedSource = ""; // track last type used

// // Toggle dropdown options visibility
// toggleOptionsBtn.addEventListener("click", () => {
//     optionsDropdown.classList.toggle("hidden");
//     toggleOptionsBtn.textContent = optionsDropdown.classList.contains("hidden") ? "Options ▼" : "Options ▲";
// });

// // Load available resolutions
// async function loadResolutions() {
//     try {
//         const res = await fetch("/supported");
//         const data = await res.json();

//         data.resolutions.forEach(({ width, height }) => {
//             const option = document.createElement("option");
//             option.value = `${width}x${height}`;
//             option.textContent = `${width} x ${height}`;
//             resolutionSelect.appendChild(option);
//         });
//     } catch (err) {
//         console.error("Error loading resolutions:", err);
//     }
// }

// // Connect FaceManager
// async function connectFaceManager() {
//     facemanagerStatus.textContent = "Connecting...";
//     try {
//         const resp = await fetch('/facemanager_setup');
//         const text = await resp.text();
//         if (resp.ok) {
//             facemanagerStatus.textContent = "✅ " + text;
//             facemanagerConnected = true;
//         } else {
//             facemanagerStatus.textContent = "❌ " + text;
//             facemanagerConnected = false;
//         }
//     } catch (err) {
//         facemanagerStatus.textContent = "❌ Failed: " + err.message;
//         facemanagerConnected = false;
//     }
// }

// // Connect DatabaseManager
// async function connectDatabaseManager() {
//     databasemanagerStatus.textContent = "Connecting...";
//     try {
//         const resp = await fetch('/database_setup');
//         const text = await resp.text();
//         if (resp.ok) {
//             databasemanagerStatus.textContent = "✅ " + text;
//             databasemanagerConnected = true;
//         } else {
//             databasemanagerStatus.textContent = "❌ " + text;
//             databasemanagerConnected = false;
//         }
//     } catch (err) {
//         databasemanagerStatus.textContent = "❌ Failed: " + err.message;
//         databasemanagerConnected = false;
//     }
// }

// // Enable Start button only if both managers connected
// function checkStartEnable() {
//     startBtn.disabled = !(facemanagerConnected && databasemanagerConnected);
// }

// // Unified toggle stream handler
// function toggleStream(url, source) {
//     if (!streaming || lastUsedSource !== source) {
//         video.src = url;
//         startBtn.textContent = "Stop";
//         streaming = true;
//         lastUsedSource = source;
//     } else {
//         video.src = "";
//         startBtn.textContent = "Start";
//         streaming = false;
//         lastUsedSource = "";
//     }
// }

// // Start/Stop with detect/identify
// startBtn.addEventListener('click', () => {
//     const detect = detectCheckbox.checked;
//     const identify = identifyCheckbox.checked;
//     const [width, height] = resolutionSelect.value.split('x');
//     const url = `/video_feed?detect=${detect}&identify=${identify}&width=${width}&height=${height}&fps_target=30`;
//     toggleStream(url, "start");
// });

// // Raw video feed
// videoBtn.addEventListener('click', () => {
//     const [width, height] = resolutionSelect.value.split('x');
//     const url = `/video_feed?detect=false&identify=false&width=${width}&height=${height}&fps_target=30`;
//     toggleStream(url, "video");
// });

// // Stop the stream completely
// function stopStream() {
//     video.src = "";
//     startBtn.textContent = "Start";
//     streaming = false;
//     lastUsedSource = "";
// }

// // Start the stream with current settings and resolution
// function startStreamWithCurrentSettings() {
//     const [width, height] = resolutionSelect.value.split('x');
//     let url = "";
//     if (lastUsedSource === "start") {
//         const detect = detectCheckbox.checked;
//         const identify = identifyCheckbox.checked;
//         url = `/video_feed?detect=${detect}&identify=${identify}&width=${width}&height=${height}&fps_target=30`;
//     } else if (lastUsedSource === "video") {
//         url = `/video_feed?detect=false&identify=false&width=${width}&height=${height}&fps_target=30`;
//     }
//     video.src = url;
//     startBtn.textContent = "Stop";
//     streaming = true;
// }

// // Restart the stream on resolution change
// // Auto update stream when resolution changes, only if streaming
// resolutionSelect.addEventListener("change", async () => {
//     if (!streaming || !lastUsedSource) return;

//     // Stop stream
//     video.src = "";
//     streaming = false;
//     startBtn.textContent = "Start";

//     // Wait briefly to allow clean disconnect
//     await new Promise(resolve => setTimeout(resolve, 300));

//     // Reconstruct URL
//     const [width, height] = resolutionSelect.value.split('x');
//     let url = "";

//     if (lastUsedSource === "start") {
//         const detect = detectCheckbox.checked;
//         const identify = identifyCheckbox.checked;
//         url = `/video_feed?detect=${detect}&identify=${identify}&width=${width}&height=${height}&fps_target=30`;
//     } else if (lastUsedSource === "video") {
//         url = `/video_feed?detect=false&identify=false&width=${width}&height=${height}&fps_target=30`;
//     }

//     // Restart stream
//     video.src = url;
//     streaming = true;
//     startBtn.textContent = "Stop";
// });



// async function init() {
//     await loadResolutions();
//     await connectFaceManager();
//     if (facemanagerConnected) {
//         await connectDatabaseManager();
//     }
//     checkStartEnable();
//     optionsDropdown.classList.add("hidden");
//     toggleOptionsBtn.textContent = "Options ▼";
// }

// window.onload = init;


const facemanagerStatus = document.getElementById("facemanager-status");
const databasemanagerStatus = document.getElementById("databasemanager-status");
const startBtn = document.getElementById("start-btn");
const videoBtn = document.getElementById("video-btn");
const resolutionSelect = document.getElementById("resolution-select");
const video = document.getElementById("video");

const detectCheckbox = document.getElementById("detect");
const identifyCheckbox = document.getElementById("identify");

const toggleOptionsBtn = document.getElementById("toggle-options");
const optionsDropdown = document.getElementById("options-dropdown");

const framerateSlider = document.getElementById("framerate-slider");
const framerateValue = document.getElementById("framerate-value");

let facemanagerConnected = false;
let databasemanagerConnected = false;
let streaming = false;
let lastUsedSource = "";

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

        // Set framerate slider range and default
        framerateSlider.max = data.framerate;
        framerateSlider.min = 1;
        framerateSlider.value = data.framerate;
        framerateValue.textContent = data.framerate;
    } catch (err) {
        console.error("Error loading resolutions or framerate:", err);
    }
}

// Connect FaceManager
async function connectFaceManager() {
    facemanagerStatus.textContent = "Connecting...";
    try {
        const resp = await fetch('/facemanager_setup');
        const text = await resp.text();
        if (resp.ok) {
            facemanagerStatus.textContent = "✅ " + text;
            facemanagerConnected = true;
        } else {
            facemanagerStatus.textContent = "❌ " + text;
            facemanagerConnected = false;
        }
    } catch (err) {
        facemanagerStatus.textContent = "❌ Failed: " + err.message;
        facemanagerConnected = false;
    }
}

// Connect DatabaseManager
async function connectDatabaseManager() {
    databasemanagerStatus.textContent = "Connecting...";
    try {
        const resp = await fetch('/database_setup');
        const text = await resp.text();
        if (resp.ok) {
            databasemanagerStatus.textContent = "✅ " + text;
            databasemanagerConnected = true;
        } else {
            databasemanagerStatus.textContent = "❌ " + text;
            databasemanagerConnected = false;
        }
    } catch (err) {
        databasemanagerStatus.textContent = "❌ Failed: " + err.message;
        databasemanagerConnected = false;
    }
}

// Enable Start button only if both managers connected
function checkStartEnable() {
    startBtn.disabled = !(facemanagerConnected && databasemanagerConnected);
}

// Unified toggle stream handler
function toggleStream(url, source) {
    if (!streaming || lastUsedSource !== source) {
        video.src = url;
        startBtn.textContent = "Stop";
        streaming = true;
        lastUsedSource = source;
    } else {
        video.src = "";
        startBtn.textContent = "Start";
        streaming = false;
        lastUsedSource = "";
    }
}

// Start/Stop with detect/identify
startBtn.addEventListener('click', () => {
    const detect = detectCheckbox.checked;
    const identify = identifyCheckbox.checked;
    const [width, height] = resolutionSelect.value.split('x');
    const fps = framerateSlider.value;
    const url = `/video_feed?detect=${detect}&identify=${identify}&width=${width}&height=${height}&fps_target=${fps}`;
    toggleStream(url, "start");
});

// Raw video feed
videoBtn.addEventListener('click', () => {
    const [width, height] = resolutionSelect.value.split('x');
    const fps = framerateSlider.value;
    const url = `/video_feed?detect=false&identify=false&width=${width}&height=${height}&fps_target=${fps}`;
    toggleStream(url, "video");
});

// Stop the stream completely
function stopStream() {
    video.src = "";
    startBtn.textContent = "Start";
    streaming = false;
    lastUsedSource = "";
}

// Start the stream with current settings and resolution/framerate
function startStreamWithCurrentSettings() {
    const [width, height] = resolutionSelect.value.split('x');
    const fps = framerateSlider.value;
    let url = "";
    if (lastUsedSource === "start") {
        const detect = detectCheckbox.checked;
        const identify = identifyCheckbox.checked;
        url = `/video_feed?detect=${detect}&identify=${identify}&width=${width}&height=${height}&fps_target=${fps}`;
    } else if (lastUsedSource === "video") {
        url = `/video_feed?detect=false&identify=false&width=${width}&height=${height}&fps_target=${fps}`;
    }
    video.src = url;
    startBtn.textContent = "Stop";
    streaming = true;
}

// Restart the stream on resolution change
resolutionSelect.addEventListener("change", async () => {
    if (!streaming || !lastUsedSource) return;
    video.src = "";
    streaming = false;
    startBtn.textContent = "Start";
    await new Promise(resolve => setTimeout(resolve, 300));
    startStreamWithCurrentSettings();
});

// Handle framerate slider UI and restart on mouseup only
framerateSlider.addEventListener("input", () => {
    framerateValue.textContent = framerateSlider.value;
});

framerateSlider.addEventListener("mouseup", async () => {
    if (!streaming || !lastUsedSource) return;
    video.src = "";
    streaming = false;
    startBtn.textContent = "Start";
    await new Promise(resolve => setTimeout(resolve, 300));
    startStreamWithCurrentSettings();
});

async function init() {
    await loadResolutions();
    await connectFaceManager();
    if (facemanagerConnected) {
        await connectDatabaseManager();
    }
    checkStartEnable();
    optionsDropdown.classList.add("hidden");
    toggleOptionsBtn.textContent = "Options ▼";
}

window.onload = init;

// Initially hide dropdown options
optionsDropdown.style.display = "none";
toggleOptionsBtn.textContent = "Options ▼";

const canvas = document.getElementById("videoCanvas");
const ctx = canvas.getContext("2d");

startBtn.addEventListener('click', () => {
    const detect = detectCheckbox.checked;
    const identify = identifyCheckbox.checked;
    const socket = new WebSocket(`ws://localhost:9253/ws/video_feed?detect=${detect}&identify=${identify}&fps_target=30`);
    socket.binaryType = "arraybuffer";

    socket.onmessage = (event) => {
        const blob = new Blob([event.data], {type: 'image/jpeg'});
        const url = URL.createObjectURL(blob);

        const img = new Image();
        img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            URL.revokeObjectURL(url);  // cleanup
        };
        img.src = url;
    };
});
