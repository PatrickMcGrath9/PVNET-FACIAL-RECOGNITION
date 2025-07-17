document.addEventListener("DOMContentLoaded", () => {
    const idList = document.getElementById("id-list");
    const facePreview = document.getElementById("face-preview");
    const nameInput = document.getElementById("name-input");
    const saveBtn = document.getElementById("save-btn");

    let selectedId = null;

    // Populate IDs (placeholder)
    // This should fetch from backend
    const dummyIds = ["unknown_001", "unknown_002", "unknown_003"];
    dummyIds.forEach(id => {
        const li = document.createElement("li");
        li.textContent = id;
        li.addEventListener("click", () => {
            selectedId = id;
            saveBtn.disabled = false;
            nameInput.value = "";
            // TODO: load image from backend and draw to canvas
        });
        idList.appendChild(li);
    });

    saveBtn.addEventListener("click", () => {
        const name = nameInput.value.trim();
        if (!name || !selectedId) return;

        // TODO: send name and ID to backend
        console.log(`Saving name "${name}" for ${selectedId}`);
    });
});
