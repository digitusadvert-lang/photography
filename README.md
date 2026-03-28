# 📸 Photographer Photo Approval System

A complete web-based system for photographers to share edited photos with customers while controlling download access.

## Features

### For Photographers
- **Session Management**: Create separate sessions for each customer/photoshoot
- **Photo Upload**: Bulk upload edited photos to sessions
- **Automatic Watermarking**: Uploaded photos are automatically watermarked for preview
- **Flexible Approval**: Approve individual photos or entire sessions at once
- **Unique Customer Links**: Generate secure, unique links for each customer
- **Dashboard**: View all sessions, photo counts, and approval status

### For Customers
- **Easy Access**: View photos via unique link (no login required)
- **Preview Photos**: View watermarked full-size images
- **Download Control**: Download original high-resolution photos only after photographer approval
- **Clear Status**: See which photos are approved and ready for download

## How It Works

### Complete Workflow

**Step 1: Photographer Uploads Photos**
1. Photographer logs into system at `http://localhost:5000` (or your server IP)
2. Creates a new session for the customer
3. In the session page, clicks **"Choose Photos"** button
4. Selects photos from computer (can select multiple at once)
5. Clicks **"Upload Photos"**
6. System automatically:
   - Saves original high-res photos to `static/uploads/` folder
   - Creates watermarked preview versions in `static/watermarked/` folder
   - Stores photo information in database

**Step 2: Share with Customer**
1. Photographer copies the unique customer access link from the session page
2. Sends link to customer via email, WhatsApp, SMS, etc.
   - Example link: `http://yourserver.com/view/xJ9kL2mP3nQ4rS5tU6vW7xY8zA1bB2c`

**Step 3: Customer Views Photos**
1. Customer opens the link (no login required)
2. Sees all photos with **"PREVIEW - NOT APPROVED"** watermark
3. All photos show **"🔒 Download Not Available"** status
4. Customer can browse and review all photos

**Step 4: Payment & Approval**
1. Customer pays photographer (outside the system - cash/bank transfer/etc.)
2. Photographer logs in and approves photos:
   - **Option A**: Click **"✓ Approve All Photos"** for entire session
   - **Option B**: Approve individual photos one by one
3. Approval is instant - customer sees changes immediately

**Step 5: Customer Downloads**
1. Customer refreshes the page or clicks back to their link
2. Approved photos now show:
   - **"⬇ Download Original"** button on each photo (downloads single photo)
   - **"📦 Download All Approved Photos (ZIP)"** button at top (downloads all as ZIP file)
3. Downloads are full high-resolution original files (no watermark)
4. Customer can download multiple times - no limits

### Download Methods for Customer

**Individual Download:**
- Click "Download Original" on any approved photo
- Gets the single high-res file
- Good for: Selecting specific favorites

**Bulk Download (ZIP):**
- Click "Download All Approved Photos (ZIP)" at top of page
- Gets all approved photos in one ZIP file
- ZIP filename includes session name: `Wedding-John_Jane_Photos.zip`
- Good for: Getting entire collection at once

## Handling Large Sessions (80-200+ Photos)

### How ZIP Files Work

The system is optimized for **large wedding sessions** (up to 2GB+):

**Automatic ZIP Generation:**
- When you click **"✓ Approve All Photos"**, system automatically creates ZIP file
- ZIP is saved to disk at `static/downloads/`
- Customer gets instant download (no waiting/timeout)

**Manual ZIP Generation:**
- Use **"📦 Generate ZIP"** button to create/recreate ZIP file
- Shows file size after generation
- Useful if you approve more photos later

**Performance:**
- ✅ Handles 200+ photos (2GB+) without issues
- ✅ No RAM/memory limits
- ✅ No browser timeouts
- ✅ Customer can resume download if interrupted
- ✅ ZIP file cached - instant downloads for customers

### Typical File Sizes

**Professional Wedding Photography:**
- High quality JPEG: 5-15 MB per photo
- Maximum quality JPEG: 10-25 MB per photo
- 50 photos ≈ 500 MB ZIP file
- 100 photos ≈ 1 GB ZIP file
- 200 photos ≈ 2 GB ZIP file

**Server Storage Requirements:**
- Original photos: ~1-2 GB per 100-photo session
- Watermarked copies: ~500 MB per 100-photo session
- ZIP file: ~1-2 GB per 100-photo session
- **Total**: ~3-5 GB per large wedding session

## Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Setup Steps

1. **Extract/Clone the system** to your desired location

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the application**:
```bash
python app.py
```

4. **Access the system**:
   - Open your browser and go to: `http://localhost:5000`
   - Default login credentials:
     - Username: `admin`
     - Password: `admin123`

## Usage Guide

### First Time Setup

1. **Login** with default credentials (admin/admin123)
2. **Change your password** (recommended - you can modify this in the database)

### Creating a Session

1. Click **"+ New Session"** on the dashboard
2. Fill in:
   - **Session Name**: Descriptive name (e.g., "Birthday Party - Sarah")
   - **Customer Name**: Client's name
   - **Customer Email**: (Optional) For your reference
3. Click **"Create Session"**

### Uploading Photos

1. Open the session from your dashboard
2. Click **"Choose Photos"** or drag & drop files
3. Select multiple photos (JPG, PNG, JPEG, GIF, HEIC)
4. Click **"Upload Photos"**
5. Photos will be automatically watermarked with "PREVIEW - NOT APPROVED"

### Sharing with Customer

1. In the session page, find the **"Customer Access Link"**
2. Click **"Copy Link"**
3. Send this link to your customer via email, WhatsApp, etc.
4. Customer can access photos without login

### Approving Photos

**Option 1: Approve All**
- Click **"✓ Approve All Photos"** button at the top

**Option 2: Individual Approval**
- Click **"Approve"** button on each photo you want to release
- You can also **"Unapprove"** photos if needed

### Customer Experience

When customers open their link:
1. They see all photos with watermarks
2. Pending photos show "🔒 Download Not Available"
3. Approved photos show "⬇ Download Original" button
4. Clicking download gives them the original high-resolution file

## File Storage Locations

### Where Files Are Stored

**Original High-Resolution Photos:**
- Location: `static/uploads/`
- Format: Original filename with timestamp prefix
- Example: `20250328_143022_wedding_photo_001.jpg`
- These are the files customers download when approved
- Size: 5-25 MB per photo (typical wedding photography)

**Watermarked Preview Photos:**
- Location: `static/watermarked/`
- Format: Same as original with `wm_` prefix
- Example: `wm_20250328_143022_wedding_photo_001.jpg`
- These are shown to customers before approval
- Size: Similar to originals (~5-25 MB)

**ZIP Download Files:**
- Location: `static/downloads/`
- Format: Session name with timestamp
- Example: `Wedding_John_Jane_20250328_143022.zip`
- Contains all approved original photos
- Size: 200 MB - 2 GB+ depending on photo count
- Auto-generated when you approve all photos

**Database:**
- Location: `photographer.db` (SQLite file in root directory)
- Stores: Sessions, photos metadata, approval status, access tokens, ZIP paths

### Backup Recommendations

For safety, regularly backup:
1. `photographer.db` - All your session and photo records
2. `static/uploads/` - All original high-res photos (CRITICAL - this is customer deliverables)
3. `static/watermarked/` - Watermarked previews (optional, can be regenerated)
4. `static/downloads/` - ZIP files (optional, can be regenerated)

**Recommended backup schedule:**
- After every session upload: Backup `static/uploads/` and database
- Weekly: Full backup of entire system
- Before deleting old sessions: Archive to external drive

**Storage space planning:**
- Small session (20 photos): ~200 MB
- Medium session (50 photos): ~500 MB  
- Large session (100 photos): ~1-2 GB
- Very large session (200 photos): ~2-4 GB
- Plan for 3x storage (originals + watermarks + ZIPs)

## File Structure

```
photographer_system/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── photographer.db                 # SQLite database (created on first run)
├── static/
│   ├── css/
│   │   └── style.css              # All styling
│   ├── js/
│   │   └── photographer.js        # Frontend interactions
│   ├── uploads/                   # Original photos (created on first run)
│   ├── watermarked/               # Watermarked previews (created on first run)
│   └── downloads/                 # ZIP files for bulk download (created on first run)
└── templates/
    ├── login.html                 # Login page
    ├── dashboard.html             # Photographer dashboard
    ├── create_session.html        # New session form
    ├── manage_session.html        # Session management
    └── customer_view.html         # Customer photo gallery
```

## Database Schema

### Tables

**photographer**
- id, username, password_hash, email, created_at

**sessions**
- id, session_name, customer_name, customer_email, access_token, created_at, approved_all, zip_path, zip_generated_at, photographer_id

**photos**
- id, session_id, filename, original_path, watermarked_path, approved, uploaded_at

## Security Features

- Passwords are hashed using Werkzeug's security functions
- Unique access tokens for each session (32-byte URL-safe tokens)
- Photos protected - originals only downloadable when approved
- Watermarked previews prevent unauthorized downloads
- Session-based authentication for photographers

## Customization

### Change Watermark Text
Edit `app.py` line 57:
```python
def create_watermark(image_path, output_path, watermark_text="YOUR TEXT HERE"):
```

### Change Upload Limits
Edit `app.py` lines 15-16:
```python
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'heic'}
```

### Change Port
Edit `app.py` last line:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## Troubleshooting

### Photos not watermarking
- Ensure Pillow is installed: `pip install Pillow`
- Check that the font file exists: `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`
- On Windows, the system will fall back to default font

### Can't upload photos
- Check file size (default max: 50MB)
- Ensure file extension is allowed
- Verify `static/uploads/` directory has write permissions

### Customer can't access link
- Verify the full URL is shared
- Check that the session still exists
- Ensure the server is running and accessible

## Production Deployment

For production use:

1. **Change secret key** in `app.py`:
```python
app.secret_key = 'your-secure-random-key-here'
```

2. **Set debug to False**:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

3. **Use a production server** (e.g., Gunicorn):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

4. **Set up HTTPS** using nginx/Apache as reverse proxy

5. **Regular backups** of `photographer.db` and `static/uploads/`

## System Requirements

- **RAM**: 512MB minimum, 1GB recommended
- **Storage**: Depends on photo volume (estimate 5-10MB per photo)
- **OS**: Windows, macOS, Linux
- **Browser**: Modern browser (Chrome, Firefox, Safari, Edge)

## Support

For issues or questions:
1. Check this README
2. Review error messages in the console
3. Ensure all dependencies are installed
4. Verify file permissions

## License

This system is provided as-is for photographers to use and modify as needed.

---

**Built with Flask, SQLite, and Pillow** 📸
