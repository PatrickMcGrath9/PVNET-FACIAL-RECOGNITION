import sqlite3, json
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import load_img, img_to_array

# ─── CONFIG ────────────────────────────────────────────────────────────────────
DB_PATH    = "facial_recognition.db"
IMG_SIZE   = (100, 100)
BATCH_SIZE = 16
EPOCHS     = 10

# ─── 1) OPEN DB & FETCH LABELS ────────────────────────────────────────────────
conn   = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT person_id, label FROM people")
people = cursor.fetchall()  # e.g. [("p1","Alice"), ("p2","Bob"), ...]

# build a mapping from label→integer index
label_to_index = {
    label: idx
    for idx, (_pid, label) in enumerate(people)
}

# ─── 2) LOAD & PREPROCESS ALL IMAGES ─────────────────────────────────────────
X_data, y_data = [], []

for person_id, label in people:
    cursor.execute(
        "SELECT image_path FROM faces WHERE person_id=?",
        (person_id,)
    )
    paths = [row[0] for row in cursor.fetchall()]

    for p in paths:
        img = load_img(p, target_size=IMG_SIZE)
        arr = img_to_array(img) / 255.0
        X_data.append(arr)
        y_data.append(label_to_index[label])

# stack into numpy arrays
X = np.stack(X_data)               # shape = (N, H, W, 3)
y = np.array(y_data, dtype=int)    # shape = (N,)

# ─── 3) DEFINE & COMPILE MODEL ────────────────────────────────────────────────
model = models.Sequential([
    layers.Input(shape=IMG_SIZE + (3,)),
    layers.Conv2D(32, (3,3), activation='relu'),
    layers.MaxPooling2D((2,2)),
    layers.Conv2D(64, (3,3), activation='relu'),
    layers.MaxPooling2D((2,2)),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(len(label_to_index), activation='softmax'),
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

# ─── 4) TRAIN ────────────────────────────────────────────────────────────────
model.fit(
    X, y,
    validation_split=0.2,
    batch_size=BATCH_SIZE,
    epochs=EPOCHS,
)

# ─── 5) (OPTIONAL) SAVE MODEL & CLOSE DB ──────────────────────────────────────
model.save('face_cnn_model.h5')
conn.close()
print("✅ Training complete, model saved to face_cnn_model.h5")
