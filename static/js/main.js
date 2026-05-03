const cameraSelect = document.getElementById("camera-select");
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

// Toggle dropdown options visibility
toggleOptionsBtn.addEventListener("click", () => {
    optionsDropdown.classList.toggle("hidden");
    toggleOptionsBtn.textContent = optionsDropdown.classList.contains("hidden") ? "Options ▼" : "Options ▲";
});

async function initializeVideoSettings(){
    try{
        if(cameraSelect.value == ""){
            return
        } 
        const [camera_id, handler_id] = cameraSelect.value.split("@", 2);
        const resp = await fetch(`/video_feed/initial_video_settings?handler_id=${handler_id}&camera_id=${camera_id}`);
        if (resp.ok) {
            const initialSettings = await resp.json();
            if (initialSettings !== null){
                if ("framerate" in initialSettings){
                    const framerate = initialSettings["framerate"]
                    framerateValue.innerHTML = framerate
                    framerateSlider.max = framerate
                    framerateSlider.value = framerate;
                }
                if ("resolutions" in initialSettings){
                    const resolutions = initialSettings["resolutions"]
                    resolutionSelect.innerHTML = ``;
                    for (const resolution of resolutions) {
                        const option = document.createElement("option");
                        option.value = `${resolution.width}x${resolution.height}`;
                        option.textContent = `${resolution.width} x ${resolution.height}`;
                        resolutionSelect.appendChild(option);
                    }
                }
                if("contrast" in initialSettings){
                    contrastSlider.value = initialSettings["contrast"]
                }
                if("gamma" in initialSettings){
                    gammaSlider.value = initialSettings["gamma"]
                }                
            }
        }
        await updateVideo();
    }
    catch(err){
        console.error(err);
    }
}

function startStream(){
    let isDrawing = false;
    let latestFrame = null;
    const video_capture_index = cameraSelect.value;
    const [width, height] = resolutionSelect.value.split('x');
    const [camera_id, handler_id] = cameraSelect.value.split("@", 2);
    const url = `/video_feed?handler_id=${handler_id}&camera_id=${camera_id}`;
    canvas.width = parseInt(width);
    canvas.height = parseInt(height);
    currentSocket = new WebSocket(url);
    currentSocket.binaryType = "arraybuffer";
    currentSocket.onmessage = (event) => {
        if (isDrawing) {
            // Drop the frame if one is currently being drawn
            latestFrame = event.data;
            return;
        }

        drawFrame(event.data);
    };

    function drawFrame(data) {
        isDrawing = true;

        const blob = new Blob([data], { type: 'image/jpeg' });
        const url = URL.createObjectURL(blob);
        const img = new Image();

        img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            URL.revokeObjectURL(url);

            // If a newer frame came in during rendering, draw it now
            if (latestFrame) {
                const frame = latestFrame;
                latestFrame = null;
                drawFrame(frame);
            }
        };

        img.onerror = (e) => {
            console.error("Image failed to load", e);
            URL.revokeObjectURL(url);
        };

        img.src = url;
        isDrawing = false;
    }

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

cameraSelect.addEventListener("change", initializeVideoSettings);
// Handle resolution change
resolutionSelect.addEventListener("change", updateVideo);
// Handle framerate change
framerateSlider.addEventListener("mouseup", updateVideo);
// Handle contrast change
contrastSlider.addEventListener("mouseup", updateVideo);
// Handle gamma change
gammaSlider.addEventListener("mouseup", updateVideo);

async function updateVideo() {
    if (currentSocket) {
        currentSocket.close();
        currentSocket = null;
    }
    const [width, height] = resolutionSelect.value.split('x');
    const fps = framerateSlider.value;
    const contrast = contrastSlider.value;
    const gamma = gammaSlider.value;
    const [camera_id, handler_id] = cameraSelect.value.split("@", 2);
    const update = {width:width, height:height, fps_target:fps, contrast:contrast, gamma:gamma}
    try {
        const resp = await fetch(`/video_feed/update_camera?handler_id=${handler_id}&camera_id=${camera_id}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(update)
        });

        const data = await resp.json();

        if (!resp.ok || "error" in data) {
            console.error("Error updating camera:", data.error || "Unknown error");
        }
    } catch (error) {
        console.error("Fetch error:", error);
    }
    startStream();
}

// Update framerate value display
framerateSlider.addEventListener("input", () => {
    framerateValue.textContent = framerateSlider.value;
});