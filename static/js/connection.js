export var facemanagerConnected = false;

// Connect FaceManager
export async function connectFaceManager() {
    try {
        const resp = await fetch('/facemanager_setup');
        if (resp.ok) {
            facemanagerConnected = true;
        } else {
            facemanagerConnected = false;
        }
        return resp.text();
    } catch (err) {
        facemanagerConnected = false;
    }
    return "";
}