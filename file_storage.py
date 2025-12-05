"""
File Storage Utilities for LMS
Provides a unified interface for file storage that can work with both local and cloud storage.
"""

import os
import uuid
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

class FileStorageManager:
    """Manages file storage operations with support for both local and future cloud storage."""
    
    def __init__(self, base_upload_folder='attached_assets'):
        """
        Initialize the file storage manager.
        
        Args:
            base_upload_folder (str): Base directory for file uploads
        """
        self.base_upload_folder = base_upload_folder
        self.allowed_video_extensions = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'}
        self.allowed_image_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        self.max_file_size = 500 * 1024 * 1024  # 500MB for videos
        self.max_image_size = 5 * 1024 * 1024   # 5MB for images
        
    def is_allowed_file(self, filename, file_type='video'):
        """
        Check if file extension is allowed.
        
        Args:
            filename (str): Name of the file
            file_type (str): Type of file ('video' or 'image')
            
        Returns:
            bool: True if file extension is allowed
        """
        if not '.' in filename:
            return False
            
        ext = filename.rsplit('.', 1)[1].lower()
        
        if file_type == 'video':
            return ext in self.allowed_video_extensions
        elif file_type == 'image':
            return ext in self.allowed_image_extensions
        else:
            return False
    
    def generate_unique_filename(self, original_filename):
        """
        Generate a unique filename using UUID to prevent conflicts.
        
        Args:
            original_filename (str): Original filename
            
        Returns:
            str: Unique filename with original extension
        """
        if '.' in original_filename:
            ext = original_filename.rsplit('.', 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
        else:
            unique_name = str(uuid.uuid4().hex)
            
        return unique_name
    
    def create_date_based_path(self, file_type='video'):
        """
        Create a date-based directory structure for file organization.
        
        Args:
            file_type (str): Type of file ('video' or 'image')
            
        Returns:
            str: Path to the date-based directory
        """
        today = datetime.now()
        date_path = os.path.join(
            self.base_upload_folder,
            file_type + 's',  # 'videos' or 'images'
            str(today.year),
            f"{today.month:02d}",
            f"{today.day:02d}"
        )
        return date_path
    
    def save_file(self, file, file_type='video'):
        """
        Save a file to local storage with improved organization.
        
        Args:
            file (FileStorage): File to save
            file_type (str): Type of file ('video' or 'image')
            
        Returns:
            dict: Information about the saved file
        """
        if not isinstance(file, FileStorage):
            raise ValueError("File must be a Werkzeug FileStorage object")
            
        # Validate file
        if not file.filename:
            raise ValueError("No file selected")
            
        # Check file extension
        if not self.is_allowed_file(file.filename, file_type):
            raise ValueError(f"File type not allowed for {file_type}")
            
        # Check file size
        max_size = self.max_image_size if file_type == 'image' else self.max_file_size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > max_size:
            size_mb = max_size / (1024 * 1024)
            raise ValueError(f"File too large. Maximum size is {size_mb}MB")
            
        # Generate unique filename
        secure_name = secure_filename(file.filename)
        unique_filename = self.generate_unique_filename(secure_name)
        
        # Create directory structure
        upload_path = self.create_date_based_path(file_type)
        os.makedirs(upload_path, exist_ok=True)
        
        # Full file path
        full_file_path = os.path.join(upload_path, unique_filename)
        
        # Save file
        file.save(full_file_path)
        
        # Calculate file hash for integrity verification
        file_hash = self.calculate_file_hash(full_file_path)
        
        # Return file information
        return {
            'filename': unique_filename,
            'original_filename': file.filename,
            'filepath': full_file_path,
            'url': full_file_path.replace('\\', '/'),  # For web access
            'size': file_size,
            'hash': file_hash,
            'upload_timestamp': datetime.now().isoformat()
        }
    
    def calculate_file_hash(self, filepath):
        """
        Calculate SHA256 hash of a file for integrity verification.
        
        Args:
            filepath (str): Path to the file
            
        Returns:
            str: SHA256 hash of the file
        """
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def delete_file(self, filepath):
        """
        Delete a file from storage.
        
        Args:
            filepath (str): Path to the file to delete
            
        Returns:
            bool: True if file was deleted, False otherwise
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {filepath}: {e}")
            return False

# Create a global instance for use in the application
file_storage_manager = FileStorageManager()