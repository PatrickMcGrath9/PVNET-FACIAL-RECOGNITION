import subprocess
import time

while True:
    # Run encoding script to update encodings.pkl
    print("Running encoding script...")
    encoding_process = subprocess.run(["python", "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/test_encoding.py"])

    if encoding_process.returncode == 0:
        print("Encoding completed successfully.")
    else:
        print("Encoding failed. Retrying in 10 seconds...")
        time.sleep(10)
        continue

    # Start the facial recognition script
    print("Starting facial recognition...")
    recognition_process = subprocess.Popen(["python", "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/test_recognition_gpu.py"])

    # Wait for recognition process to complete or restart if it stops
    recognition_process.wait()
    print("Facial recognition script exited. Restarting encoding and recognition...")
    time.sleep(2)  # Short delay before restarting
