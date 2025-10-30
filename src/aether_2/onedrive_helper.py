import requests
import os
import json
import logging
from urllib.parse import urlparse, parse_qs
from pathlib import Path

logger = logging.getLogger('aether_2')

class OneDriveDownloader:
    """Helper class to download files from OneDrive"""
    
    def __init__(self, access_token=None, client_id=None, client_secret=None):
        self.access_token = access_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://graph.microsoft.com/v1.0"
    
    def download_from_share_link(self, share_link, output_directory="inputs/"):
        """
        Download file from OneDrive share link (simplest method)
        
        Args:
            share_link (str): OneDrive share link
            output_directory (str): Directory to save downloaded files
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.makedirs(output_directory, exist_ok=True)
            
            # Convert share link to direct download URL
            direct_url = self._convert_share_link(share_link)
            
            if not direct_url:
                logger.error("❌ Could not convert share link to direct download URL")
                return False
            
            # Download file
            response = requests.get(direct_url, stream=True)
            
            if response.status_code == 200:
                # Extract filename from URL or headers
                filename = self._get_filename_from_response(response, share_link)
                filepath = os.path.join(output_directory, filename)
                
                # Download file in chunks
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"✅ Downloaded: {filename}")
                return True
            else:
                logger.error(f"❌ Failed to download. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error downloading from {share_link}: {e}")
            return False
    
    def download_from_graph_api(self, file_id, output_directory="inputs/"):
        """
        Download file using Microsoft Graph API (requires authentication)
        
        Args:
            file_id (str): OneDrive file ID
            output_directory (str): Directory to save downloaded files
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.access_token:
            logger.error("❌ Access token required for Graph API method")
            return False
        
        try:
            os.makedirs(output_directory, exist_ok=True)
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Get file metadata
            metadata_url = f"{self.base_url}/me/drive/items/{file_id}"
            response = requests.get(metadata_url, headers=headers)
            
            if response.status_code == 200:
                file_info = response.json()
                file_name = file_info['name']
                
                # Download file content
                download_url = f"{self.base_url}/me/drive/items/{file_id}/content"
                file_response = requests.get(download_url, headers=headers)
                
                if file_response.status_code == 200:
                    filepath = os.path.join(output_directory, file_name)
                    with open(filepath, 'wb') as f:
                        f.write(file_response.content)
                    
                    logger.info(f"✅ Downloaded: {file_name}")
                    return True
                else:
                    logger.error(f"❌ Failed to download file. Status: {file_response.status_code}")
                    return False
            else:
                logger.error(f"❌ Failed to get file metadata. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error downloading file {file_id}: {e}")
            return False
    
    def download_folder_contents(self, folder_id, output_directory="inputs/"):
        """
        Download all files from a OneDrive folder
        
        Args:
            folder_id (str): OneDrive folder ID
            output_directory (str): Directory to save downloaded files
            
        Returns:
            list: List of successfully downloaded filenames
        """
        if not self.access_token:
            logger.error("❌ Access token required for folder download")
            return []
        
        try:
            os.makedirs(output_directory, exist_ok=True)
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Get folder contents
            folder_url = f"{self.base_url}/me/drive/items/{folder_id}/children"
            response = requests.get(folder_url, headers=headers)
            
            if response.status_code == 200:
                folder_contents = response.json()
                downloaded_files = []
                
                for item in folder_contents.get('value', []):
                    if 'file' in item:  # It's a file, not a folder
                        file_id = item['id']
                        file_name = item['name']
                        
                        # Download each file
                        if self.download_from_graph_api(file_id, output_directory):
                            downloaded_files.append(file_name)
                
                logger.info(f"✅ Downloaded {len(downloaded_files)} files from folder")
                return downloaded_files
            else:
                logger.error(f"❌ Failed to get folder contents. Status: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error downloading folder {folder_id}: {e}")
            return []
    
    def _convert_share_link(self, share_link):
        """Convert OneDrive share link to direct download URL"""
        try:
            # Handle different OneDrive link formats
            if 'onedrive.live.com' in share_link:
                # Extract file ID from share link
                file_id = self._extract_file_id_from_share_link(share_link)
                if file_id:
                    return f"https://api.onedrive.com/v1.0/shares/{file_id}/root/content"
            
            elif 'sharepoint.com' in share_link:
                # SharePoint link - more complex conversion needed
                return self._convert_sharepoint_link(share_link)
            
            else:
                logger.warning(f"⚠️ Unsupported link format: {share_link}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error converting share link: {e}")
            return None
    
    def _extract_file_id_from_share_link(self, share_link):
        """Extract file ID from OneDrive share link"""
        try:
            # Parse URL to extract file ID
            parsed_url = urlparse(share_link)
            path_parts = parsed_url.path.split('/')
            
            # Look for file ID in URL path
            for part in path_parts:
                if len(part) > 20 and '!' in part:  # OneDrive file IDs typically contain '!'
                    return part
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extracting file ID: {e}")
            return None
    
    def _convert_sharepoint_link(self, share_link):
        """Convert SharePoint link to direct download URL"""
        # This is a simplified version - SharePoint links are more complex
        # You might need to use Graph API for SharePoint links
        logger.warning("⚠️ SharePoint link conversion not fully implemented")
        return None
    
    def _get_filename_from_response(self, response, original_link):
        """Extract filename from response headers or original link"""
        try:
            # Try to get filename from Content-Disposition header
            content_disposition = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
                return filename
            
            # Fallback: extract from URL
            parsed_url = urlparse(original_link)
            filename = os.path.basename(parsed_url.path)
            
            # If no filename found, use default
            if not filename or filename == '/':
                filename = f"downloaded_file_{hash(original_link)}.json"
            
            return filename
            
        except Exception as e:
            logger.error(f"❌ Error extracting filename: {e}")
            return f"downloaded_file_{hash(original_link)}.json"


def download_inputs_from_onedrive(share_links, input_directory="inputs/"):
    """
    Main function to download multiple files from OneDrive
    
    Args:
        share_links (list): List of OneDrive share links
        input_directory (str): Directory to save downloaded files
        
    Returns:
        list: List of successfully downloaded filenames
    """
    downloader = OneDriveDownloader()
    downloaded_files = []
    
    logger.info(f"🔄 Starting download of {len(share_links)} files from OneDrive")
    
    for i, link in enumerate(share_links, 1):
        logger.info(f"📁 Downloading file {i}/{len(share_links)}")
        
        if downloader.download_from_share_link(link, input_directory):
            downloaded_files.append(link)
        else:
            logger.error(f"❌ Failed to download: {link}")
    
    logger.info(f"✅ Download completed. Successfully downloaded {len(downloaded_files)} files")
    return downloaded_files


# Example usage and configuration
def setup_onedrive_config():
    """
    Setup OneDrive configuration
    Returns a dictionary with configuration options
    """
    config = {
        # Method 1: Share Links (Simplest - No authentication required)
        "share_links": [
            "https://onedrive.live.com/redir?resid=YOUR_FILE_ID&authkey=YOUR_AUTH_KEY",
            # Add more share links here
        ],
        
        # Method 2: Graph API (Requires authentication)
        "graph_api": {
            "access_token": None,  # Will be set after authentication
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "tenant_id": "YOUR_TENANT_ID",
            "folder_id": "YOUR_FOLDER_ID",  # OneDrive folder ID
        },
        
        # Method 3: Direct file IDs (Requires authentication)
        "file_ids": [
            "YOUR_FILE_ID_1",
            "YOUR_FILE_ID_2",
            # Add more file IDs here
        ]
    }
    
    return config


if __name__ == "__main__":
    # Example usage
    config = setup_onedrive_config()
    
    # Method 1: Download using share links
    if config["share_links"]:
        downloaded = download_inputs_from_onedrive(config["share_links"])
        print(f"Downloaded {len(downloaded)} files")
    
    # Method 2: Download using Graph API (requires authentication)
    # downloader = OneDriveDownloader(access_token="YOUR_ACCESS_TOKEN")
    # downloaded = downloader.download_folder_contents("YOUR_FOLDER_ID")
