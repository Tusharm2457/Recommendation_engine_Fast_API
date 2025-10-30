# OneDrive Integration Setup Guide

## Overview
This guide explains how to set up OneDrive integration to automatically download JSON input files for your recommendation pipeline.

## Method 1: Share Links (Recommended - Simplest)

### What You Need:
- **OneDrive share links** for your JSON files
- **No authentication** required

### How to Get Share Links:
1. Go to your OneDrive folder
2. Right-click on each JSON file
3. Select "Share" → "Copy link"
4. Make sure the link is set to "Anyone with the link can view"

### Example Share Link Format:
```
https://onedrive.live.com/redir?resid=ABC123!456&authkey=XYZ789
```

### Usage:
```python
from src.aether_2.onedrive_helper import download_inputs_from_onedrive

# Your OneDrive share links
share_links = [
    "https://onedrive.live.com/redir?resid=ABC123!456&authkey=XYZ789",
    "https://onedrive.live.com/redir?resid=DEF456!789&authkey=UVW012",
]

# Download all files
downloaded = download_inputs_from_onedrive(share_links)
```

---

## Method 2: Microsoft Graph API (Advanced)

### What You Need:
- **Azure App Registration**
- **Client ID** and **Client Secret**
- **Tenant ID** (for OneDrive for Business)
- **Folder ID** or **File IDs**

### Step 1: Create Azure App Registration
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "Azure Active Directory" → "App registrations"
3. Click "New registration"
4. Fill in:
   - **Name**: "Recommendation Gen OneDrive"
   - **Supported account types**: Choose based on your needs
   - **Redirect URI**: `http://localhost:8080` (for testing)
5. Click "Register"

### Step 2: Get Required IDs
After registration, you'll get:
- **Application (client) ID**: `12345678-1234-1234-1234-123456789012`
- **Directory (tenant) ID**: `87654321-4321-4321-4321-210987654321`

### Step 3: Create Client Secret
1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Add description: "OneDrive Access"
4. Set expiration (recommend 12 months)
5. Click "Add"
6. **Copy the secret value immediately** (you won't see it again)

### Step 4: Set API Permissions
1. Go to "API permissions"
2. Click "Add a permission"
3. Select "Microsoft Graph"
4. Choose "Application permissions"
5. Add these permissions:
   - `Files.Read.All`
   - `Sites.Read.All`
6. Click "Grant admin consent"

### Step 5: Get OneDrive Folder/File IDs

#### For Personal OneDrive:
1. Go to [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
2. Sign in with your Microsoft account
3. Use this query to get your drive info:
   ```
   GET https://graph.microsoft.com/v1.0/me/drive
   ```
4. Use this query to list folder contents:
   ```
   GET https://graph.microsoft.com/v1.0/me/drive/root/children
   ```

#### For OneDrive for Business:
1. Get your site ID:
   ```
   GET https://graph.microsoft.com/v1.0/sites/{your-domain}.sharepoint.com:/sites/{site-name}
   ```
2. List folder contents:
   ```
   GET https://graph.microsoft.com/v1.0/sites/{site-id}/drive/root/children
   ```

### Usage:
```python
from src.aether_2.onedrive_helper import OneDriveDownloader

# Initialize with your credentials
downloader = OneDriveDownloader(
    access_token="YOUR_ACCESS_TOKEN",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET"
)

# Download specific file
downloader.download_from_graph_api("FILE_ID", "inputs/")

# Download entire folder
downloader.download_folder_contents("FOLDER_ID", "inputs/")
```

---

## Method 3: OneDrive for Business (Enterprise)

### What You Need:
- **SharePoint site URL**
- **Site ID**
- **Folder path**
- **Service Principal** or **App Registration**

### Getting SharePoint Site ID:
1. Go to your SharePoint site
2. The URL format is: `https://{tenant}.sharepoint.com/sites/{site-name}`
3. Use Graph API to get site ID:
   ```
   GET https://graph.microsoft.com/v1.0/sites/{tenant}.sharepoint.com:/sites/{site-name}
   ```

### Usage:
```python
from src.aether_2.onedrive_helper import OneDriveDownloader

downloader = OneDriveDownloader(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET"
)

# Download from SharePoint
downloader.download_from_sharepoint("SITE_ID", "folder/path/file.json", "inputs/")
```

---

## Integration with Main Pipeline

### Option 1: Download Before Processing
```python
# In your main.py
from src.aether_2.onedrive_helper import download_inputs_from_onedrive

def run_with_onedrive_download():
    # Download files first
    share_links = [
        "https://onedrive.live.com/redir?resid=ABC123!456&authkey=XYZ789",
        # Add more links
    ]
    
    downloaded = download_inputs_from_onedrive(share_links, "inputs/")
    
    if downloaded:
        # Process downloaded files
        run_batch("inputs/")
    else:
        logger.error("❌ No files downloaded from OneDrive")
```

### Option 2: Automatic Download on Startup
```python
# Add to your main.py startup
def initialize_inputs():
    """Download inputs from OneDrive if inputs folder is empty"""
    if not os.listdir("inputs/"):
        logger.info("📁 Inputs folder empty, downloading from OneDrive...")
        download_inputs_from_onedrive(YOUR_SHARE_LINKS)
    else:
        logger.info("📁 Inputs folder has files, skipping OneDrive download")
```

---

## Troubleshooting

### Common Issues:

1. **"Access denied" errors**
   - Check if share links are set to "Anyone with the link can view"
   - Verify API permissions are granted

2. **"File not found" errors**
   - Verify file IDs are correct
   - Check if files still exist in OneDrive

3. **"Authentication failed" errors**
   - Verify client ID and secret are correct
   - Check if client secret has expired
   - Ensure admin consent is granted

4. **"Rate limit exceeded" errors**
   - Add delays between requests
   - Use batch processing for multiple files

### Testing Your Setup:
```python
# Test share link download
from src.aether_2.onedrive_helper import OneDriveDownloader

downloader = OneDriveDownloader()
success = downloader.download_from_share_link("YOUR_SHARE_LINK", "test_downloads/")
print(f"Download successful: {success}")
```

---

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for sensitive data
3. **Rotate client secrets** regularly
4. **Use least privilege** permissions
5. **Monitor API usage** for unusual activity

### Environment Variables Setup:
```bash
# Add to your .env file
ONEDRIVE_CLIENT_ID=your_client_id
ONEDRIVE_CLIENT_SECRET=your_client_secret
ONEDRIVE_TENANT_ID=your_tenant_id
ONEDRIVE_FOLDER_ID=your_folder_id
```

---

## Next Steps

1. **Choose your method** (Share Links recommended for simplicity)
2. **Get your OneDrive links/IDs** following the steps above
3. **Test the download** with a single file
4. **Integrate with your pipeline** using the examples provided
5. **Set up monitoring** to track download success/failure

For questions or issues, check the logs in `logs/crewai_debug.log` for detailed error information.
