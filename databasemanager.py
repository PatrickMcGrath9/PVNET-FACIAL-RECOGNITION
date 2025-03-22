import os
import cv2

class DatabaseManager:
    def __init__(self, audit_dir="DB/audit"):
        """Initialize the DatabaseManager with a directory for audit images."""
        self.audit_dir = audit_dir
        if not os.path.exists(self.audit_dir):
            os.makedirs(self.audit_dir)  # Create the directory if it doesn’t exist

    def save_unknown_face(self, image, group_id):
        """Save the face image to the audit directory with a unique filename."""
        filename = f"unknown_group_{group_id}.jpg"
        filepath = os.path.join(self.audit_dir, filename)
        cv2.imwrite(filepath, image)  # Save the image in BGR format