// import { connectDatabaseManager, connectFaceManager, facemanagerConnected, databasemanagerConnected } from "./connection.js";

// async function loadUnknownFaces() {
//     const container = document.getElementById("unknown-faces-container");
//     container.innerHTML = ""; // clear previous

//     try {
//         const response = await fetch("/audit/get_unknown");
//         const data = await response.json();

//         // data.faces is expected to be an array
//         const unknownFaces = data.faces || [];

//         unknownFaces.forEach((item) => {
//             const card = document.createElement("div");
//             card.className = "face-card";

//             const img = document.createElement("img");
//             img.src = item.image_url; // updated to match server field

//             const input = document.createElement("input");
//             input.placeholder = "Enter name";
//             input.dataset.faceId = item.uid; // updated to match server field

//             const button = document.createElement("button");
//             button.textContent = "Assign Name";
//             button.onclick = async () => {
//                 const name = input.value.trim();
//                 if (!name) {
//                     alert("Please enter a name.");
//                     return;
//                 }
//                 try {
//                     const resp = await fetch("/audit", {
//                         method: "PATCH",
//                         headers: { "Content-Type": "application/json" },
//                         body: JSON.stringify({ id: item.uid, name }), // updated field
//                     });
//                     if (resp.ok) {
//                         alert("Name assigned!");
//                         card.remove();
//                     } else {
//                         alert("Failed to assign name.");
//                     }
//                 } catch (e) {
//                     console.error(e);
//                     alert("Error assigning name.");
//                 }
//             };

//             card.appendChild(img);
//             card.appendChild(input);
//             card.appendChild(button);
//             container.appendChild(card);
//         });

//         if (unknownFaces.length === 0) {
//             container.textContent = "No unknown faces to audit.";
//         }
//     } catch (err) {
//         console.error("Failed to load unknown faces:", err);
//         container.textContent = "Error loading unknown faces.";
//     }
// }

// async function init(){
//     const fm_resp = await connectFaceManager();
//     if (facemanagerConnected) {
//         const db_resp = await connectDatabaseManager();
//     }
//     await fetch('/audit/get_db_ip');

//     loadUnknownFaces();
// }

// window.onload = init;

async function loadUnknownFaces() {
    const container = document.getElementById("unknown-faces-container");
    container.innerHTML = ""; // Clear previous content

    try {
        const response = await fetch("/audit/get_unknown");
        if (!response.ok) {
            throw new Error(`Failed to load unknown faces: HTTP ${response.status} - ${await response.text()}`);
        }
        const data = await response.json();

        // Handle single object or array response
        const unknownFaces = Array.isArray(data.faces) ? data.faces : [data];

        if (unknownFaces.length === 0) {
            container.textContent = "No unknown faces to audit.";
            return;
        }

        unknownFaces.forEach((item) => {
            const card = document.createElement("div");
            card.className = "face-card";

            const img = document.createElement("img");
            img.src = item.image; // Use 'image' field from response
            img.onerror = () => {
                img.alt = "Failed to load image";
                console.error(`Image load failed for ID: ${item.id}`);
            };

            const input = document.createElement("input");
            input.placeholder = "Enter name";
            input.dataset.faceId = item.id;

            const button = document.createElement("button");
            button.textContent = "Assign Name";
            button.onclick = async () => {
                const label = input.value.trim();
                if (!label) {
                    alert("Please enter a name.");
                    return;
                }
                try {
                    const resp = await fetch("/audit/update_unknown", {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ id: item.id, label }),
                    });
                    if (resp.ok) {
                        alert("Name assigned!");
                        card.remove();
                    } else {
                        alert(`Failed to assign name: ${await resp.text()}`);
                    }
                } catch (e) {
                    console.error("Error assigning name:", e);
                    alert("Error assigning name.");
                }
            };

            card.appendChild(img);
            card.appendChild(input);
            card.appendChild(button);
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Failed to load unknown faces:", err);
        container.textContent = `Error loading unknown faces: ${err.message}`;
    }
}

async function init() {
    try {
        // Load unknown faces
        await loadUnknownFaces();
    } catch (err) {
        console.error("Initialization error:", err);
        const container = document.getElementById("unknown-faces-container");
        container.textContent = `Initialization error: ${err.message}`;
    }
}

window.onload = init;