import face_recognition
import os
import pickle

# Path to the database
database_path = "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/Database"


# Load existing encodings if they exist, if not initiallize them
if os.path.exists("encodings.pkl"):
    with open("encodings.pkl", "rb") as f:
        known_face_encodings, known_face_names, processed_images = pickle.load(f)
else:
    #Store new face encoding
    known_face_encodings = []
    #Store the name associated to the encoding
    known_face_names = []
    #See which images are already processed
    processed_images = set()

# Calculate the total number of images in the database
total_images = 0
for person_name in os.listdir(database_path):
    person_folder = os.path.join(database_path, person_name)
    if os.path.isdir(person_folder):
        total_images += len([name for name in os.listdir(person_folder) if name.endswith(('.jpg', '.jpeg', '.png'))])
print(f"total image in database are {total_images}")

# Initialize the counter of how many images are already encoded
encoded_count = len(processed_images)
print(f"We encoded {encoded_count} image, we should be encoding {total_images-encoded_count} more image")

processed_count = 0
skip_count = 0
# Loop over each person in the database
for person_name in os.listdir(database_path):
    person_folder = os.path.join(database_path, person_name)

    # Check if the folder is a directory (to skip any files accidentally placed in the root folder)
    if os.path.isdir(person_folder):
        for image_name in os.listdir(person_folder):
            if image_name.endswith(('.jpg', '.jpeg', '.png')):
                print(f"Looking at {image_name}")
                image_path = os.path.join(person_folder, image_name)

                # Convert to a relative path based on the root of the database to make tracking image easier
                relative_image_path = os.path.relpath(image_path, database_path)

                # Skip if the image has already been processed
                if relative_image_path in processed_images:
                    skip_count += 1
                    print(f"this was already encoded, skipcount = {skip_count}")
                    continue

                print(f"processing {image_name}...")

                # Load the image file and learn how to recognize it
                image = face_recognition.load_image_file(image_path)
                face_encodings = face_recognition.face_encodings(image)

                # Store the encodings and the name
                encode_only_first = 0
                for face_encoding in face_encodings:
                    if encode_only_first == 0:
                        known_face_encodings.append(face_encoding)
                        known_face_names.append(person_name)
                        processed_images.add(relative_image_path)

                        # Update the counter and display progress
                        encoded_count += 1
                        processed_count += 1
                        print(f"Encoded {encoded_count}/{total_images} images, AND this is the {processed_count}th encoded from this run.")
                    encode_only_first += 1

# Save the encodings, names, and processed image paths to a file
with open("encodings.pkl", "wb") as f:
    pickle.dump((known_face_encodings, known_face_names, processed_images), f)

print("Encodings and names have been saved to 'encodings.pkl'.")
