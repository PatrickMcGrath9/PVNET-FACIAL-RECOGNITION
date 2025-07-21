export var facemanagerConnected = false;
export var databasemanagerConnected = false;

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
}

// Connect DatabaseManager
export async function connectDatabaseManager() {
    try {
        const resp = await fetch('/database_setup');
        if (resp.ok) {
            databasemanagerConnected = true;
        } else {
            databasemanagerConnected = false;
        }
        return resp.text();
    } catch (err) {
        databasemanagerConnected = false;
    } 
}