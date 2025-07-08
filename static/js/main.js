// const facemanagerStatus = document.getElementById("facemanager-status");
// const databasemanagerStatus = document.getElementById("databasemanager-status");
// const startBtn = document.getElementById("start-btn");
// const video = document.getElementById("video");

// const detectCheckbox = document.getElementById("detect");
// const identifyCheckbox = document.getElementById("identify");

// let facemanagerConnected = false;
// let databasemanagerConnected = false;

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

// function checkStartEnable() {
//     if (facemanagerConnected && databasemanagerConnected) {
//         startBtn.disabled = false;
//         facemanagerStatus.textContent += " (Ready)";
//         databasemanagerStatus.textContent += " (Ready)";
//     } else {
//         startBtn.disabled = true;
//     }
// }

// async function init() {
//     await connectFaceManager();
//     if (facemanagerConnected) {
//         await connectDatabaseManager();
//     }
//     checkStartEnable();
// }

// startBtn.addEventListener('click', () => {
//     const detect = detectCheckbox.checked;
//     const identify = identifyCheckbox.checked;
//     video.src = `/video_feed?detect=${detect}&identify=${identify}&fps_target=30`;
// });


// window.onload = init;


// const facemanagerStatus = document.getElementById("facemanager-status");
// const databasemanagerStatus = document.getElementById("databasemanager-status");
// const startBtn = document.getElementById("start-btn");
// const video = document.getElementById("video");

// const detectCheckbox = document.getElementById("detect");
// const identifyCheckbox = document.getElementById("identify");

// const toggleOptionsBtn = document.getElementById("toggle-options");
// const optionsDropdown = document.getElementById("options-dropdown");

// let facemanagerConnected = false;
// let databasemanagerConnected = false;

// // Toggle dropdown visibility
// toggleOptionsBtn.addEventListener("click", () => {
//     const isVisible = optionsDropdown.style.display === "block";
//     optionsDropdown.style.display = isVisible ? "none" : "block";
//     toggleOptionsBtn.textContent = isVisible ? "Options ▼" : "Options ▲";
// });

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

// function checkStartEnable() {
//     if (facemanagerConnected && databasemanagerConnected) {
//         startBtn.disabled = false;
//         facemanagerStatus.textContent += " (Ready)";
//         databasemanagerStatus.textContent += " (Ready)";
//     } else {
//         startBtn.disabled = true;
//     }
// }

// async function init() {
//     await connectFaceManager();
//     if (facemanagerConnected) {
//         await connectDatabaseManager();
//     }
//     checkStartEnable();
// }

// startBtn.addEventListener('click', () => {
//     const detect = detectCheckbox.checked;
//     const identify = identifyCheckbox.checked;
//     video.src = `/video_feed?detect=${detect}&identify=${identify}&fps_target=30`;
// });

// window.onload = init;


const facemanagerStatus = document.getElementById("facemanager-status");
const databasemanagerStatus = document.getElementById("databasemanager-status");
const startBtn = document.getElementById("start-btn");
const video = document.getElementById("video");

const detectCheckbox = document.getElementById("detect");
const identifyCheckbox = document.getElementById("identify");

const toggleOptionsBtn = document.getElementById("toggle-options");
const optionsDropdown = document.getElementById("options-dropdown");

let facemanagerConnected = false;
let databasemanagerConnected = false;

// Toggle dropdown options visibility
toggleOptionsBtn.addEventListener("click", () => {
    const isVisible = optionsDropdown.style.display === "block";
    optionsDropdown.style.display = isVisible ? "none" : "block";
    toggleOptionsBtn.textContent = isVisible ? "Options ▼" : "Options ▲";
});

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
    if (facemanagerConnected && databasemanagerConnected) {
        startBtn.disabled = false;
        if (!facemanagerStatus.textContent.includes("(Ready)")) {
          facemanagerStatus.textContent += " (Ready)";
        }
        if (!databasemanagerStatus.textContent.includes("(Ready)")) {
          databasemanagerStatus.textContent += " (Ready)";
        }
    } else {
        startBtn.disabled = true;
    }
}

// Initialize connections
async function init() {
    await connectFaceManager();
    if (facemanagerConnected) {
        await connectDatabaseManager();
    }
    checkStartEnable();
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