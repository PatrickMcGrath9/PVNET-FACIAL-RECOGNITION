
// // async function loadUnknownFaces() {
// //     const container = document.getElementById("unknown-faces-container");
// //     container.innerHTML = ""; // Clear previous content

// //     try {
// //         const response = await fetch("/audit/get_unknown");
// //         if (!response.ok) {
// //             throw new Error(`Failed to load unknown faces: HTTP ${response.status} - ${await response.text()}`);
// //         }
// //         const data = await response.json();

// //         // Handle single object or array response
// //         const unknownFaces = Array.isArray(data.faces) ? data.faces : [data];

// //         if (unknownFaces.length === 0) {
// //             container.textContent = "No unknown faces to audit.";
// //             return;
// //         }

// //         unknownFaces.forEach((item) => {
// //             const card = document.createElement("div");
// //             card.className = "face-card";

// //             const img = document.createElement("img");
// //             img.src = item.image; // Use 'image' field from response
// //             img.onerror = () => {
// //                 img.alt = "Failed to load image";
// //                 console.error(`Image load failed for ID: ${item.id}`);
// //             };

// //             const input = document.createElement("input");
// //             input.placeholder = "Enter name";
// //             input.dataset.faceId = item.id;

// //             const button = document.createElement("button");
// //             button.textContent = "Assign Name";
// //             button.onclick = async () => {
// //                 const label = input.value.trim();
// //                 if (!label) {
// //                     alert("Please enter a name.");
// //                     return;
// //                 }
// //                 try {
// //                     const resp = await fetch("/audit/update_unknown", {
// //                         method: "PATCH",
// //                         headers: { "Content-Type": "application/json" },
// //                         body: JSON.stringify({ id: item.id, label }),
// //                     });
// //                     if (resp.ok) {
// //                         alert("Name assigned!");
// //                         card.remove();
// //                     } else {
// //                         alert(`Failed to assign name: ${await resp.text()}`);
// //                     }
// //                 } catch (e) {
// //                     console.error("Error assigning name:", e);
// //                     alert("Error assigning name.");
// //                 }
// //             };

// //             card.appendChild(img);
// //             card.appendChild(input);
// //             card.appendChild(button);
// //             container.appendChild(card);
// //         });
// //     } catch (err) {
// //         console.error("Failed to load unknown faces:", err);
// //         container.textContent = `Error loading unknown faces: ${err.message}`;
// //     }
// // }

// // async function init() {
// //     try {
// //         // Load unknown faces
// //         await loadUnknownFaces();
// //     } catch (err) {
// //         console.error("Initialization error:", err);
// //         const container = document.getElementById("unknown-faces-container");
// //         container.textContent = `Initialization error: ${err.message}`;
// //     }
// // }

// // window.onload = init;

// async function loadUnknownFaces() {
//     const container = document.getElementById("unknown-faces-container");
//     container.innerHTML = ""; // Clear previous content

//     try {
//         const response = await fetch("/audit/get_unknown", {
//             headers: { "Cache-Control": "no-cache" } // Prevent caching
//         });
//         if (!response.ok) {
//             throw new Error(`Failed to load unknown faces: HTTP ${response.status} - ${await response.text()}`);
//         }
//         const data = await response.json();

//         // Check if the response contains an error
//         if (data.error) {
//             container.textContent = data.error || "No unknown faces to audit.";
//             return;
//         }

//         // Handle the single face object directly (server returns one object, not an array)
//         const item = data;
//         const card = document.createElement("div");
//         card.className = "face-card";

//         const img = document.createElement("img");
//         img.src = item.image; // Use 'image' field from response
//         img.onerror = () => {
//             img.alt = "Failed to load image";
//             console.error(`Image load failed for ID: ${item.id}`);
//         };

//         const input = document.createElement("input");
//         input.placeholder = "Enter name";
//         input.dataset.faceId = item.id;

//         const button = document.createElement("button");
//         button.textContent = "Assign Name";
//         button.onclick = async () => {
//             const label = input.value.trim();
//             if (!label) {
//                 alert("Please enter a name.");
//                 return;
//             }
//             try {
//                 const resp = await fetch("/audit/update_unknown", {
//                     method: "PATCH",
//                     headers: { "Content-Type": "application/json" },
//                     body : JSON.stringify({ id: item.id, label })
//                 });
//                 if (resp.ok) {
//                     alert("Name assigned!");
//                     card.remove();
//                     await loadUnknownFaces(); // Immediately fetch the next unknown face
//                 } else {
//                     alert(`Failed to assign name: ${await resp.text()}`);
//                 }
//             } catch (e) {
//                 console.error("Error assigning name:", e);
//                 alert("Error assigning name.");
//             }
//         };

//         card.appendChild(img);
//         card.appendChild(input);
//         card.appendChild(button);
//         container.appendChild(card);
//     } catch (err) {
//         console.error("Failed to load unknown faces:", err);
//         container.textContent = `Error loading unknown faces: ${err.message}`;
//     }
// }

// async function init() {
//     try {
//         await loadUnknownFaces();
//     } catch (err) {
//         console.error("Initialization error:", err);
//         const container = document.getElementById("unknown-faces-container");
//         container.textContent = `Initialization error: ${err.message}`;
//     }
// }

// window.onload = init;

async function loadUnknownFaces() {
    const container = document.getElementById("unknown-faces-container");
    container.innerHTML = ""; // Clear previous content

    try {
        const response = await fetch("/audit/get_unknown", {
            headers: { "Cache-Control": "no-cache" }
        });
        if (!response.ok) {
            throw new Error(`Failed to load unknown faces: HTTP ${response.status} - ${await response.text()}`);
        }
        const data = await response.json();

        if (data.error) {
            container.textContent = data.error || "No unknown faces to audit.";
            return;
        }

        const item = data.unknown;
        const labels = data.labels;

        const card = document.createElement("div");
        card.className = "face-card";

        const img = document.createElement("img");
        img.src = item.image;
        img.onerror = () => {
            img.alt = "Failed to load image";
            console.error(`Image load failed for ID: ${item.id}`);
        };

        const select = document.createElement("select");
        select.innerHTML = '<option value="">Select a name</option>' +
                           '<option value="new">New Name</option>' +
                           labels.map(label => `<option value="${label}">${label}</option>`).join('');

        const input = document.createElement("input");
        input.placeholder = "Enter new name";
        input.style.display = "none"; // Hidden by default

        select.onchange = () => {
            if (select.value === "new") {
                input.style.display = "block";
            } else {
                input.style.display = "none";
            }
        };

        const button = document.createElement("button");
        button.textContent = "Assign Name";
        button.onclick = async () => {
            let label;
            if (select.value === "new") {
                label = input.value.trim();
            } else {
                label = select.value;
            }
            if (!label) {
                alert("Please select a name or enter a new one.");
                return;
            }
            try {
                const resp = await fetch("/audit/update_unknown", {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ id: item.id, label })
                });
                if (resp.ok) {
                    alert("Name assigned!");
                    card.remove();
                    await loadUnknownFaces(); // Fetch the next unknown face and updated labels
                } else {
                    alert(`Failed to assign name: ${await resp.text()}`);
                }
            } catch (e) {
                console.error("Error assigning name:", e);
                alert("Error assigning name.");
            }
        };

        card.appendChild(img);
        card.appendChild(select);
        card.appendChild(input);
        card.appendChild(button);
        container.appendChild(card);
    } catch (err) {
        console.error("Failed to load unknown faces:", err);
        container.textContent = `Error loading unknown faces: ${err.message}`;
    }
}

async function init() {
    try {
        await loadUnknownFaces();
    } catch (err) {
        console.error("Initialization error:", err);
        const container = document.getElementById("unknown-faces-container");
        container.textContent = `Initialization error: ${err.message}`;
    }
}

window.onload = init;