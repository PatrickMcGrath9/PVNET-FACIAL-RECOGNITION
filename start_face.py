# import subprocess
# import time
# import logging

# # Set up logging
# logging.basicConfig(
#     filename="program_face_log2.log",  # Log file name
#     level=logging.INFO,  # Logging level: INFO, WARNING, ERROR, etc.
#     format="%(asctime)s - %(levelname)s - %(message)s",  # Log message format
# )

# def log_and_print(message, level="info"):
#     """Log a message and print it to the console."""
#     if level == "info":
#         logging.info(message)
#     elif level == "warning":
#         logging.warning(message)
#     elif level == "error":
#         logging.error(message)
#     print(message)

# try:
#     # Log the start of the encoding script
#     log_and_print("Starting encoding script...")

#     # Run the encoding script
#     encoding_process = subprocess.run(
#         ["python", "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/test_encoding.py"],
#         check=True
#     )

#     log_and_print("Encoding completed successfully.")

#     # Log the start of the recognition script
#     log_and_print("Starting facial recognition...")
#     recognition_process = subprocess.Popen(
#         ["python", "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/test_recognition_gpu.py"]
#     )

#     # Wait for the recognition process to finish
#     recognition_process.wait()
#     log_and_print("Facial recognition script exited. Restarting encoding and recognition...")
#     time.sleep(2)

# except subprocess.CalledProcessError as e:
#     log_and_print(f"Error while running the encoding script: {e}", level="error")
#     log_and_print("Retrying in 10 seconds...")
#     time.sleep(10)

# except Exception as e:
#     log_and_print(f"Unexpected error: {e}", level="error")
#     log_and_print("Restarting program...")
#     time.sleep(5)

import subprocess
import time
import logging
import psutil
import os
import signal

# Set up logging
logging.basicConfig(
    filename="program_face_log2.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
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

def kill_existing_python_processes(script_name):
    """Kill any running instances of the given script to prevent duplicates."""
    for process in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        try:
            cmdline = process.info["cmdline"]
            if cmdline and "python" in cmdline[0].lower() and script_name in " ".join(cmdline):
                log_and_print(f"Terminating existing process: {cmdline}")
                process.terminate()  # Graceful termination
                time.sleep(1)
                if psutil.pid_exists(process.pid):
                    process.kill()  # Force kill if still running
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

try:
    # Ensure old processes are terminated
    kill_existing_python_processes("test_recognition_gpu.py")

    log_and_print("Starting encoding script...")
    encoding_process = subprocess.run(
        ["python", "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/test_encoding.py"],
        check=True
    )
    log_and_print("Encoding completed successfully.")

    log_and_print("Starting facial recognition...")
    recognition_process = subprocess.Popen(
        ["python", "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/test_recognition_gpu.py"]
    )

    # Wait for recognition process to finish
    recognition_process.wait()
    log_and_print("Facial recognition script exited. Restarting in 2 seconds...")
    time.sleep(2)

except subprocess.CalledProcessError as e:
    log_and_print(f"Error while running the encoding script: {e}", level="error")
    time.sleep(10)

except Exception as e:
    log_and_print(f"Unexpected error: {e}", level="error")
    time.sleep(5)

finally:
    # Ensure recognition process is terminated
    if "recognition_process" in locals() and recognition_process.poll() is None:
        log_and_print("Terminating facial recognition process...")
        recognition_process.terminate()
        time.sleep(2)
        if recognition_process.poll() is None:
            recognition_process.kill()
        log_and_print("Facial recognition process terminated.")
