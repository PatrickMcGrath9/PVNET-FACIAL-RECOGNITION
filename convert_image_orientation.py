import os
from PIL import Image, ExifTags

def correct_image_orientation(image_path):
    # Open the image file
    img = Image.open(image_path)

    # Attempt to fix the orientation based on EXIF
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break

        exif = img._getexif()
        if exif is not None:
            orientation = exif.get(orientation, 1)

            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)

        # Save the corrected image (overwrite the original)
        img.save(image_path)

    except (AttributeError, KeyError, IndexError) as e:
        # If there's no EXIF data, save without any transformations
        img.save(image_path)

def process_folder(root_folder):
    # Iterate through all subfolders and files
    for subdir, _, files in os.walk(root_folder):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(subdir, file)
                print(f"Processing {file_path}")
                correct_image_orientation(file_path)

# Example usage
process_folder('Database')




#
# with Image.open('Database/Joshua/Joshua1.jpg') as img:
#     # Save without EXIF data
#     img.save('Joshua1_right.jpg', exif=None)
#
# with Image.open('Database/Joshua/Joshua2.jpg') as img:
#     # Save without EXIF data
#     img.save('Database/Joshua/Joshua2_right.jpg', exif=None)
#
# with Image.open('Database/Joshua/Joshua3.jpg') as img:
#     # Save without EXIF data
#     img.save('Database/Joshua/Joshua3_right.jpg', exif=None)