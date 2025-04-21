import dropbox
from pathlib import Path
import os
import requests
import json
import time

class DropboxOAuth2:
    """Class to handle Dropbox OAuth2 refresh token workflow"""
    def __init__(self, refresh_token, app_key, app_secret):
        self.refresh_token = refresh_token
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = None
        self.expiration_time = 0

    def get_access_token(self):
        """Get a valid access token, refreshing if necessary"""
        current_time = time.time()
        
        # Check if access token is expired or not set
        if self.access_token is None or current_time >= self.expiration_time:
            self._refresh_access_token()
        
        return self.access_token
    
    def _refresh_access_token(self):
        """Refresh the access token using the refresh token"""
        try:
            # Prepare the request to refresh the token
            url = "https://api.dropboxapi.com/oauth2/token"
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.app_key,
                "client_secret": self.app_secret
            }
            
            # Make the request
            response = requests.post(url, data=data)
            response_data = response.json()
            
            if response.status_code == 200 and "access_token" in response_data:
                self.access_token = response_data["access_token"]
                # Set expiration time (default token lifetime is 4 hours = 14400 seconds)
                expires_in = response_data.get("expires_in", 14400)
                # Set expiration time with a small buffer
                self.expiration_time = time.time() + expires_in - 300  # 5 minutes buffer
                print("Successfully refreshed Dropbox access token")
                return True
            else:
                print(f"Failed to refresh token: {response.text}")
                return False
        except Exception as e:
            print(f"Error refreshing access token: {e}")
            return False

def get_dropbox_client(oauth_config):
    """Initialize and return a Dropbox client
    
    Args:
        oauth_config: Either a refresh token dictionary with 'refresh_token', 'app_key', 'app_secret'
                     or a direct access token string
    """
    try:
        # Check if oauth_config is a dictionary with refresh token details
        if isinstance(oauth_config, dict) and 'refresh_token' in oauth_config:
            oauth_handler = DropboxOAuth2(
                oauth_config['refresh_token'],
                oauth_config['app_key'],
                oauth_config['app_secret']
            )
            # Get a fresh access token
            access_token = oauth_handler.get_access_token()
            if access_token:
                return dropbox.Dropbox(access_token)
            else:
                print("Failed to obtain access token from refresh token")
                return None
        # If it's just an access token string (backward compatibility)
        elif isinstance(oauth_config, str):
            return dropbox.Dropbox(oauth_config)
        else:
            print("Invalid OAuth configuration format")
            return None
    except Exception as e:
        print(f"Error creating Dropbox client: {e}")
        return None

def upload_to_dropbox(dbx, local_file_path, dropbox_path):
    """Upload a file to Dropbox"""
    try:
        # Read the local file
        with open(local_file_path, 'rb') as f:
            file_content = f.read()
        
        # Upload to Dropbox
        dbx.files_upload(
            file_content,
            dropbox_path,
            mode=dropbox.files.WriteMode.overwrite
        )
        print(f"Successfully uploaded to Dropbox: {dropbox_path}")
        return True
    except Exception as e:
        print(f"Failed to upload to Dropbox: {e}")
        return False