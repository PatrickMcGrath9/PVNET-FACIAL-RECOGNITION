import subprocess
import time
import logging

# Set up logging
logging.basicConfig(
    filename="program_face_log.log",  # Log file name
    level=logging.INFO,  # Logging level: INFO, WARNING, ERROR, etc.
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log message format
)

def log_and_print(message, level="info"):
    """Log a message and print it to the console."""
    if level == "info":
        logging.info(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)
    print(message)

while True:
    try:
        # Log the start of the encoding script
        log_and_print("Starting encoding script...")

        # Run the encoding script
        encoding_process = subprocess.run(
            ["python", "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/test_encoding.py"],
            check=True
        )

        log_and_print("Encoding completed successfully.")

        # Log the start of the recognition script
        log_and_print("Starting facial recognition...")
        recognition_process = subprocess.Popen(
            ["python", "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/test_recognition_gpu.py"]
        )

        # Wait for the recognition process to finish
        recognition_process.wait()
        log_and_print("Facial recognition script exited. Restarting encoding and recognition...")
        time.sleep(2)

    except subprocess.CalledProcessError as e:
        log_and_print(f"Error while running the encoding script: {e}", level="error")
        log_and_print("Retrying in 10 seconds...")
        time.sleep(10)

    except Exception as e:
        log_and_print(f"Unexpected error: {e}", level="error")
        log_and_print("Restarting program...")
        time.sleep(5)
