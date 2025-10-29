"""
AWS S3 service for file upload and management.

This module provides functions for uploading, downloading, and managing files
in AWS S3 buckets for product images and user avatars.
"""

import boto3
import uuid
from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException, status
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime, timedelta

from app.database import settings


class S3Service:
    """Service class for AWS S3 operations."""
    
    def __init__(self):
        """Initialize S3 service with AWS credentials."""
        if not all([settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, settings.S3_BUCKET_NAME]):
            raise ValueError("AWS credentials and S3 bucket name must be configured")
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self.base_url = settings.S3_BASE_URL or f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com"
    
    def generate_file_key(self, file_type: str, user_id: str, file_extension: str) -> str:
        """
        Generate a unique file key for S3 storage.
        
        Args:
            file_type: Type of file (product_image, avatar, etc.)
            user_id: User ID for organizing files
            file_extension: File extension (e.g., .jpg, .png)
            
        Returns:
            str: Unique file key
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{file_type}/{user_id}/{timestamp}_{unique_id}{file_extension}"
    
    def upload_file(self, file: UploadFile, file_type: str, user_id: str) -> Dict[str, Any]:
        """
        Upload a file to S3.
        
        Args:
            file: FastAPI UploadFile object
            file_type: Type of file (product_image, avatar, etc.)
            user_id: User ID for organizing files
            
        Returns:
            Dict containing file URL and metadata
            
        Raises:
            HTTPException: If upload fails
        """
        try:
            # Validate file size
            file_content = file.file.read()
            if len(file_content) > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
                )
            
            # Reset file pointer
            file.file.seek(0)
            
            # Generate file key
            file_extension = f".{file.filename.split('.')[-1]}" if '.' in file.filename else ""
            file_key = self.generate_file_key(file_type, user_id, file_extension)
            
            # Upload to S3
            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                file_key,
                ExtraArgs={
                    'ContentType': file.content_type or 'application/octet-stream'
                    # Note: ACL removed - ensure your S3 bucket has a bucket policy 
                    # that allows public read access, or use CloudFront for distribution
                }
            )
            
            # Generate file URL
            file_url = f"{self.base_url}/{file_key}"
            
            return {
                "url": file_url,
                "key": file_key,
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(file_content),
                "uploaded_at": datetime.now().isoformat()
            }
            
        except NoCredentialsError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AWS credentials not configured"
            )
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to S3: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during file upload: {str(e)}"
            )
    
    def upload_multiple_files(self, files: List[UploadFile], file_type: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Upload multiple files to S3.
        
        Args:
            files: List of FastAPI UploadFile objects
            file_type: Type of files (product_image, avatar, etc.)
            user_id: User ID for organizing files
            
        Returns:
            List of dictionaries containing file URLs and metadata
        """
        results = []
        for file in files:
            try:
                result = self.upload_file(file, file_type, user_id)
                results.append(result)
            except HTTPException as e:
                # Log error but continue with other files
                results.append({
                    "error": e.detail,
                    "filename": file.filename
                })
        
        return results
    
    def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            file_key: S3 file key to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError as e:
            print(f"Error deleting file {file_key}: {str(e)}")
            return False
    
    def generate_presigned_url(self, file_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for temporary file access.
        
        Args:
            file_key: S3 file key
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Presigned URL or None if generation fails
        """
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            print(f"Error generating presigned URL for {file_key}: {str(e)}")
            return None
    
    def get_file_metadata(self, file_key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a file in S3.
        
        Args:
            file_key: S3 file key
            
        Returns:
            Dict containing file metadata or None if not found
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return {
                "size": response.get('ContentLength'),
                "content_type": response.get('ContentType'),
                "last_modified": response.get('LastModified'),
                "etag": response.get('ETag')
            }
        except ClientError as e:
            print(f"Error getting metadata for {file_key}: {str(e)}")
            return None


# Global S3 service instance
s3_service = None

def get_s3_service() -> S3Service:
    """
    Get or create S3 service instance.
    
    Returns:
        S3Service: S3 service instance
        
    Raises:
        HTTPException: If S3 is not configured
    """
    global s3_service
    
    if s3_service is None:
        try:
            s3_service = S3Service()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 service not configured: {str(e)}"
            )
    
    return s3_service


def extract_file_key_from_url(url: str) -> Optional[str]:
    """
    Extract S3 file key from a full S3 URL.
    
    Args:
        url: Full S3 URL
        
    Returns:
        str: File key or None if URL is invalid
    """
    try:
        # Remove base URL to get the file key
        if settings.S3_BASE_URL and url.startswith(settings.S3_BASE_URL):
            return url.replace(f"{settings.S3_BASE_URL}/", "")
        elif f"{settings.S3_BUCKET_NAME}.s3." in url:
            # Extract key from standard S3 URL format
            parts = url.split(f"{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/")
            if len(parts) > 1:
                return parts[1]
        return None
    except Exception:
        return None
