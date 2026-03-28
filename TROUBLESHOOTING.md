# 🔧 Troubleshooting Download Issues

## Common Download Problems & Solutions

### Problem 1: "No approved photos available for download"

**Cause:** Photos haven't been approved by photographer yet

**Solution:**
1. Photographer must login
2. Open the session
3. Click **"✓ Approve All Photos"** OR approve photos individually
4. Customer can then download

---

### Problem 2: ZIP download button doesn't appear

**Cause:** No photos are approved yet

**Solution:**
1. Check if any photos show "Approved ✓" badge
2. If not, ask photographer to approve photos
3. Refresh the customer page after approval

---

### Problem 3: ZIP file download starts but fails/corrupts

**Possible Causes:**
- File path issues
- Permission issues
- Missing photos

**Solutions:**

1. **Check console logs** (run with `python app.py` in terminal):
   - Look for ERROR messages
   - Check which photo file is missing

2. **Verify photo files exist**:
   ```bash
   # Check if upload folder has photos
   ls -la static/uploads/
   
   # Check file permissions
   chmod -R 755 static/uploads/
   chmod -R 755 static/downloads/
   ```

3. **Test ZIP generation manually**:
   - Login as photographer
   - Open session
   - Click **"📦 Generate ZIP"** button
   - Check if file size shows (e.g., "Size: 523.4 MB")

---

### Problem 4: Browser says "Download failed" or "Network error"

**Possible Causes:**
- File too large for timeout
- Slow connection
- Server configuration

**Solutions:**

1. **Try individual photo downloads first** to test if any download works

2. **Check file size**:
   - Login as photographer
   - Look at ZIP status: "ZIP file ready (Size: X MB)"
   - If over 1GB, consider splitting session into multiple galleries

3. **Increase timeout** (in `app.py`):
   ```python
   # Add after app = Flask(__name__)
   app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
   ```

---

### Problem 5: "Invalid access link" error

**Cause:** Wrong URL or expired/deleted session

**Solution:**
1. Verify the full URL is correct
2. Check session still exists in photographer dashboard
3. Get fresh link from photographer

---

## Debugging Steps

### Step 1: Check Console Output

When you run `python app.py`, watch for these messages:

**Good messages:**
```
INFO: Download request for session 1 - Wedding Photos
INFO: Found 45 approved photos
SUCCESS: ZIP created successfully. Size: 523.4 MB
```

**Problem messages:**
```
ERROR: No approved photos for session 1
WARNING: Photo file not found: static/uploads/photo.jpg
ERROR: ZIP file not created at static/downloads/...
```

### Step 2: Verify File Locations

```bash
# Check if folders exist
ls -la static/

# Should show:
# drwxr-xr-x  uploads/
# drwxr-xr-x  watermarked/
# drwxr-xr-x  downloads/

# Check if photos are in uploads
ls static/uploads/

# Check if ZIP was created
ls static/downloads/
```

### Step 3: Test Individual Photo Download

1. Customer opens their link
2. Find any approved photo
3. Click "⬇ Download Original"
4. If this works, but ZIP doesn't, issue is with ZIP generation

### Step 4: Check Database

```bash
# Open database
sqlite3 photographer.db

# Check if photos are approved
SELECT id, filename, approved FROM photos WHERE session_id = 1;

# Should show:
# 1|photo1.jpg|1
# 2|photo2.jpg|1
# (1 = approved, 0 = not approved)

# Check if ZIP path is stored
SELECT id, session_name, zip_path FROM sessions WHERE id = 1;
```

---

## Permission Issues (Linux/Mac)

If you get permission errors:

```bash
# Give write permission to all static folders
chmod -R 755 static/

# Or more specifically:
chmod 755 static/uploads/
chmod 755 static/watermarked/
chmod 755 static/downloads/

# Make sure uploaded files are readable
chmod 644 static/uploads/*
```

---

## Windows-Specific Issues

### Problem: "Permission denied" on Windows

**Solution:**
1. Run terminal/command prompt as Administrator
2. Check if antivirus is blocking file creation
3. Ensure folders aren't read-only:
   - Right-click `static` folder → Properties
   - Uncheck "Read-only"
   - Apply to all subfolders

---

## File Size Issues

### If ZIP is too large (over 2GB):

**Option 1: Split into multiple sessions**
- Create separate sessions for different parts (e.g., "Wedding Part 1", "Wedding Part 2")

**Option 2: Deliver via cloud storage**
- Upload to Google Drive/Dropbox
- Share link with customer

**Option 3: Lower image quality** (in photo editor before upload)
- Export JPEGs at 85% quality instead of 100%
- Typical file sizes: 10-15 MB → 5-8 MB per photo

---

## Still Not Working?

### Get detailed error logs:

1. **Run in debug mode** (already enabled in `app.py`):
   ```python
   app.run(debug=True, host='0.0.0.0', port=5000)
   ```

2. **Check Python version**:
   ```bash
   python --version
   # Should be 3.11+
   ```

3. **Reinstall dependencies**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

4. **Test ZIP creation manually** in Python:
   ```python
   import zipfile
   import os
   
   # Test if you can create ZIP
   test_zip = 'test.zip'
   with zipfile.ZipFile(test_zip, 'w') as zf:
       zf.write('README.md', 'test.txt')
   
   print(f"ZIP created: {os.path.exists(test_zip)}")
   print(f"ZIP size: {os.path.getsize(test_zip)} bytes")
   ```

---

## Contact Information

If issues persist, share these details:
1. Error messages from console
2. Operating system (Windows/Mac/Linux)
3. Python version
4. Number of photos in session
5. Approximate file size
6. What step fails (upload, approval, or download)
