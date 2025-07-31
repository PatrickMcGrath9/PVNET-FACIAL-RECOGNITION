const container = document.getElementById("unknown-faces-container");
let labels = null;

import {connectFaceManager} from './connection.js'

async function updateLabels(){
    try{
        const response = await fetch("/audit/labels", {
            headers: { "Cache-Control": "no-cache" }
        });
        if(!response.ok){
            throw new Error(`Failed to update labels: HTTP ${response.status} - ${await response.text()}`);
        }
        const resp_json = await response.json();
        if(!("error" in resp_json)){
            labels = resp_json
        }
    }catch (err) {
        console.error("Failed to update labels:", err);
    }
}

async function loadNextUnknown(){
    try{
        const response = await fetch("/audit/unknown", {
            headers: { "Cache-Control": "no-cache" }
        });
        if (!response.ok) {
            throw new Error(`Failed to load unknown faces: HTTP ${response.status} - ${await response.text()}`);
        }
        const resp_json = await response.json();
        if(!("error" in resp_json)){
            return resp_json
        }
    }catch(err){
        console.error("Failed to get next unknown:", err);
    }
}

async function createUIForItem(item){
    container.innerHTML = ""; // Clear previous content
    const card = document.createElement("div");
    card.className = "face-card";

    const image = document.createElement("img");
    image.src = item.image;
    image.onerror = () => {
        image.alt = "Failed to load image";
        console.error(`Image load failed for ID: ${item.id}`);
    };

    const select = document.createElement("select");
    select.innerHTML =  '<option value="placeholder" disabled selected hidden>Select a name</option>' + '<option value="new">New Name</option>' +
                        labels.map(([id, label]) => `<option value="${id}">${label}</option>`).join('');

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
        try{
            submit(item, select, input);
        } catch(err){
            console.error("Error submitting name:", e);
            alert("Error submitting name.");
        }
        card.remove();
        await processNextItem();
    };

    card.appendChild(image);
    card.appendChild(select);
    card.appendChild(input);
    card.appendChild(button);
    container.appendChild(card);
}

async function submit(item, select, input){
    try{
        if(select.value === "placeholder"){
            alert("Please select a name or enter a new one.");
            return
        }
        else if(select.value === "new"){
            const update_value = input.value.trim();
            if(!update_value){
                alert("Please select a name or enter a new one.");
                return
            }
            const response = await fetch("/audit/unknown",{
                method: "PATCH",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({id: item.id, label: update_value})
            });
            if (!response.ok){
                throw new Error(`Failed to assign name: ${await response.text()}`)
            }
            const resp_json = await response.json();
            if("error" in resp_json){
                throw new Error(resp_json.error)
            }
        }
        else{
            const old_id = item.id
            const new_id = select.value
            const response = await fetch("/audit/unknown",{
                method: "PATCH",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({old_id, new_id})
            });
            if (!response.ok){
                throw new Error(`Failed to assign name: ${await resp.text()}`)
            }
            const resp_json = await response.json();
            if("error" in resp_json){
                throw new Error(resp_json.error)
            }
            
        }
    }catch (e) {
        throw new Error(`Failed to assign name: ${e}`)
    }
}

async function processNextItem() {
    await updateLabels();
    const item = await loadNextUnknown();
    if (item) {
        await createUIForItem(item);
    } else {
        container.innerHTML = "<p>There are no more items left.</p>";
    }
}

await connectFaceManager();
await processNextItem();