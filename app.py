from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image, ImageDraw, ImageFont
import sqlite3
import os
import secrets
from datetime import datetime
from functools import wraps
import zipfile
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['WATERMARK_FOLDER'] = 'static/watermarked'
app.config['DOWNLOAD_FOLDER'] = 'static/downloads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size per upload
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'heic'}

# Database setup
def init_db():
    conn = sqlite3.connect('photographer.db')
    c = conn.cursor()
    
    # Photographer table
    c.execute('''CREATE TABLE IF NOT EXISTS photographer
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  email TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Sessions table
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_name TEXT NOT NULL,
                  customer_name TEXT NOT NULL,
                  customer_email TEXT,
                  access_token TEXT UNIQUE NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  approved_all INTEGER DEFAULT 0,
                  zip_path TEXT,
                  zip_generated_at TIMESTAMP,
                  photographer_id INTEGER,
                  FOREIGN KEY (photographer_id) REFERENCES photographer (id))''')
    
    # Photos table
    c.execute('''CREATE TABLE IF NOT EXISTS photos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER NOT NULL,
                  filename TEXT NOT NULL,
                  original_path TEXT NOT NULL,
                  watermarked_path TEXT NOT NULL,
                  approved INTEGER DEFAULT 0,
                  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (session_id) REFERENCES sessions (id))''')
    
    # Create default photographer account if not exists
    c.execute("SELECT * FROM photographer WHERE username = 'admin'")
    if not c.fetchone():
        password_hash = generate_password_hash('admin123')
        c.execute("INSERT INTO photographer (username, password_hash, email) VALUES (?, ?, ?)",
                  ('admin', password_hash, 'admin@example.com'))
    
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def create_watermark(image_path, output_path, watermark_text="© PREVIEW ONLY"):
    """Create watermarked version of image with tiled diagonal text"""
    try:
        from PIL import Image as PILImage, ImageDraw, ImageFont
        img = PILImage.open(image_path)

        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        font_size = max(20, int(min(width, height) * 0.055))

        # Load font — try common Windows fonts first, then Linux, then built-in
        font = None
        for fp in [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/verdanab.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]:
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                continue
        if font is None:
            try:
                font = ImageFont.load_default(size=font_size)
            except TypeError:
                font = ImageFont.load_default()

        # Build overlay for tiled diagonal watermarks
        overlay = PILImage.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Measure one watermark stamp
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        tw = bbox[2] - bbox[0] + 40
        th = bbox[3] - bbox[1] + 40

        import math
        angle = -30

        # Tile watermark across the whole image
        step_x = tw + 60
        step_y = th + 80
        for row in range(-2, int(height / step_y) + 3):
            for col in range(-2, int(width / step_x) + 3):
                cx = col * step_x + (row % 2) * (step_x // 2)
                cy = row * step_y

                # Create a small image for one stamp then rotate and paste
                stamp = PILImage.new('RGBA', (tw * 2, th * 2), (0, 0, 0, 0))
                sd = ImageDraw.Draw(stamp)
                # Dark outline
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        sd.text((tw // 2 + dx, th // 2 + dy), watermark_text, font=font, fill=(0, 0, 0, 50))
                # White text
                sd.text((tw // 2, th // 2), watermark_text, font=font, fill=(255, 255, 255, 80))
                stamp = stamp.rotate(angle, expand=True)
                sw, sh = stamp.size
                overlay.paste(stamp, (cx - sw // 2, cy - sh // 2), stamp)

        img_rgba = img.convert('RGBA')
        result = PILImage.alpha_composite(img_rgba, overlay)
        result.convert('RGB').save(output_path, 'JPEG', quality=85)
        print(f"INFO: Watermark created successfully: {output_path}")
        return True
    except Exception as e:
        print(f"Error creating watermark: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_session_zip(session_id):
    """Generate ZIP file for all approved photos in a session"""
    try:
        conn = sqlite3.connect('photographer.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get session info
        c.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session = c.fetchone()
        
        if not session:
            print(f"ERROR: Session {session_id} not found")
            conn.close()
            return None
        
        print(f"INFO: Generating ZIP for session {session_id} - {session['session_name']}")
        
        # Get all approved photos
        c.execute("SELECT * FROM photos WHERE session_id = ? AND approved = 1", (session_id,))
        photos = c.fetchall()
        
        if not photos:
            print(f"ERROR: No approved photos found for session {session_id}")
            conn.close()
            return None
        
        print(f"INFO: Found {len(photos)} approved photos")
        
        # Create ZIP filename
        safe_session_name = "".join(c for c in session['session_name'] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_session_name = safe_session_name.replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"{safe_session_name}_{timestamp}.zip"
        zip_path = os.path.join(app.config['DOWNLOAD_FOLDER'], zip_filename)
        
        print(f"INFO: ZIP path: {zip_path}")
        
        # Ensure download folder exists
        os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
        print(f"INFO: Download folder exists: {os.path.exists(app.config['DOWNLOAD_FOLDER'])}")
        
        # Create ZIP file on disk
        try:
            print(f"INFO: Starting ZIP creation...")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for i, photo in enumerate(photos):
                    photo_path = photo['original_path']
                    print(f"INFO: Adding photo {i+1}/{len(photos)}: {photo_path}")
                    
                    if not os.path.exists(photo_path):
                        print(f"WARNING: Photo file not found: {photo_path}")
                        continue
                    
                    # Add photo to ZIP with original filename
                    zf.write(photo_path, arcname=photo['filename'])
            
            # Check if ZIP was created
            if not os.path.exists(zip_path):
                print(f"ERROR: ZIP file not created at {zip_path}")
                conn.close()
                return None
            
            file_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
            print(f"SUCCESS: ZIP created successfully. Size: {file_size_mb:.1f} MB")
            
            # Update session with ZIP path
            c.execute("UPDATE sessions SET zip_path = ?, zip_generated_at = ? WHERE id = ?",
                      (zip_path, datetime.now(), session_id))
            conn.commit()
            conn.close()
            
            return zip_path
            
        except Exception as e:
            print(f"ERROR creating ZIP file: {str(e)}")
            import traceback
            traceback.print_exc()
            conn.close()
            return None
            
    except Exception as e:
        print(f"EXCEPTION in generate_session_zip: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'photographer_id' not in request.cookies:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect('photographer.db')
        c = conn.cursor()
        c.execute("SELECT id, password_hash FROM photographer WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            response = redirect(url_for('dashboard'))
            response.set_cookie('photographer_id', str(user[0]))
            return response
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    response = redirect(url_for('login'))
    response.set_cookie('photographer_id', '', expires=0)
    return response

@app.route('/dashboard')
@login_required
def dashboard():
    photographer_id = request.cookies.get('photographer_id')
    
    conn = sqlite3.connect('photographer.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""SELECT s.*, COUNT(p.id) as photo_count,
                 SUM(CASE WHEN p.approved = 1 THEN 1 ELSE 0 END) as approved_count
                 FROM sessions s
                 LEFT JOIN photos p ON s.id = p.session_id
                 WHERE s.photographer_id = ?
                 GROUP BY s.id
                 ORDER BY s.created_at DESC""", (photographer_id,))
    sessions = c.fetchall()
    conn.close()
    
    return render_template('dashboard.html', sessions=sessions)

@app.route('/session/create', methods=['GET', 'POST'])
@login_required
def create_session():
    if request.method == 'POST':
        photographer_id = request.cookies.get('photographer_id')
        session_name = request.form.get('session_name')
        customer_name = request.form.get('customer_name')
        customer_email = request.form.get('customer_email')
        access_token = secrets.token_urlsafe(32)
        
        conn = sqlite3.connect('photographer.db')
        c = conn.cursor()
        c.execute("""INSERT INTO sessions (session_name, customer_name, customer_email, 
                     access_token, photographer_id) VALUES (?, ?, ?, ?, ?)""",
                  (session_name, customer_name, customer_email, access_token, photographer_id))
        session_id = c.lastrowid
        conn.commit()
        conn.close()
        
        flash('Session created successfully!', 'success')
        return redirect(url_for('manage_session', session_id=session_id))
    
    return render_template('create_session.html')

@app.route('/session/<int:session_id>')
@login_required
def manage_session(session_id):
    conn = sqlite3.connect('photographer.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session = c.fetchone()
    c.execute("SELECT * FROM photos WHERE session_id = ? ORDER BY uploaded_at DESC", (session_id,))
    photos = c.fetchall()
    conn.close()
    
    # Generate customer link
    customer_link = url_for('customer_view', token=session['access_token'], _external=True)
    
    return render_template('manage_session.html', session=session, photos=photos, customer_link=customer_link)

@app.route('/session/<int:session_id>/regenerate_watermarks', methods=['POST'])
@login_required
def regenerate_watermarks(session_id):
    """Regenerate watermarks for all photos in a session"""
    conn = sqlite3.connect('photographer.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM photos WHERE session_id = ?", (session_id,))
    photos = c.fetchall()

    success = 0
    for photo in photos:
        original_path = photo['original_path']
        if not os.path.exists(original_path):
            continue
        # Build watermarked path (always under WATERMARK_FOLDER)
        wm_filename = f"wm_{os.path.basename(original_path)}"
        watermarked_path = os.path.join(app.config['WATERMARK_FOLDER'], wm_filename).replace('\\', '/')
        if create_watermark(original_path, watermarked_path):
            c.execute("UPDATE photos SET watermarked_path = ? WHERE id = ?", (watermarked_path, photo['id']))
            success += 1

    conn.commit()
    conn.close()
    flash(f'Watermarks regenerated for {success} photos.', 'success')
    return redirect(url_for('manage_session', session_id=session_id))

@app.route('/session/<int:session_id>/upload', methods=['POST'])
@login_required
def upload_photos(session_id):
    if 'photos' not in request.files:
        return jsonify({'error': 'No photos uploaded'}), 400
    
    files = request.files.getlist('photos')
    uploaded_count = 0
    
    conn = sqlite3.connect('photographer.db')
    c = conn.cursor()
    
    for file in files:
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            
            # Save original
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename).replace('\\', '/')
            file.save(original_path)

            # Create watermarked version
            watermarked_filename = f"wm_{unique_filename}"
            watermarked_path = os.path.join(app.config['WATERMARK_FOLDER'], watermarked_filename).replace('\\', '/')
            
            watermark_ok = create_watermark(original_path, watermarked_path)
            if not watermark_ok:
                # Watermark failed — use original as fallback so photo still appears
                watermarked_path = original_path
                print(f"WARNING: Watermark failed for {filename}, using original as preview")

            # Save to database regardless of watermark result
            c.execute("""INSERT INTO photos (session_id, filename, original_path, watermarked_path)
                         VALUES (?, ?, ?, ?)""",
                      (session_id, filename, original_path, watermarked_path))
            uploaded_count += 1
    
    conn.commit()
    conn.close()
    
    flash(f'{uploaded_count} photos uploaded successfully!', 'success')
    return redirect(url_for('manage_session', session_id=session_id))

@app.route('/photo/<int:photo_id>/approve', methods=['POST'])
@login_required
def approve_photo(photo_id):
    conn = sqlite3.connect('photographer.db')
    c = conn.cursor()
    c.execute("UPDATE photos SET approved = 1 WHERE id = ?", (photo_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/photo/<int:photo_id>/unapprove', methods=['POST'])
@login_required
def unapprove_photo(photo_id):
    conn = sqlite3.connect('photographer.db')
    c = conn.cursor()
    c.execute("UPDATE photos SET approved = 0 WHERE id = ?", (photo_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/session/<int:session_id>/delete', methods=['POST'])
@login_required
def delete_session(session_id):
    conn = sqlite3.connect('photographer.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get all photos to delete their files
    c.execute("SELECT * FROM photos WHERE session_id = ?", (session_id,))
    photos = c.fetchall()
    for photo in photos:
        for path in [photo['original_path'], photo['watermarked_path']]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    # Delete ZIP file if exists
    c.execute("SELECT zip_path FROM sessions WHERE id = ?", (session_id,))
    session = c.fetchone()
    if session and session['zip_path'] and os.path.exists(session['zip_path']):
        try:
            os.remove(session['zip_path'])
        except Exception:
            pass

    # Delete DB records
    c.execute("DELETE FROM photos WHERE session_id = ?", (session_id,))
    c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

    flash('Session deleted successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/session/<int:session_id>/generate_zip', methods=['POST'])
@login_required
def generate_zip(session_id):
    zip_path = generate_session_zip(session_id)
    
    if zip_path:
        # Get file size
        file_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        flash(f'ZIP file generated successfully! Size: {file_size_mb:.1f} MB', 'success')
    else:
        flash('Failed to generate ZIP file. Make sure at least one photo is approved.', 'error')
    
    return redirect(url_for('manage_session', session_id=session_id))

@app.route('/session/<int:session_id>/approve_all', methods=['POST'])
@login_required
def approve_all(session_id):
    conn = sqlite3.connect('photographer.db')
    c = conn.cursor()
    c.execute("UPDATE photos SET approved = 1 WHERE session_id = ?", (session_id,))
    c.execute("UPDATE sessions SET approved_all = 1 WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    
    # Generate ZIP file for download
    flash('Generating ZIP file for customer download...', 'info')
    zip_path = generate_session_zip(session_id)
    
    if zip_path:
        flash('All photos approved and ZIP file ready for download!', 'success')
    else:
        flash('All photos approved! (ZIP generation will happen when customer requests download)', 'success')
    
    return redirect(url_for('manage_session', session_id=session_id))

# Customer-facing routes
@app.route('/view/<token>')
def customer_view(token):
    conn = sqlite3.connect('photographer.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE access_token = ?", (token,))
    session = c.fetchone()
    
    if not session:
        return "Invalid access link", 404
    
    c.execute("SELECT * FROM photos WHERE session_id = ? ORDER BY uploaded_at DESC", (session['id'],))
    photos = c.fetchall()
    conn.close()
    
    return render_template('customer_view.html', session=session, photos=photos)

@app.route('/download/<int:photo_id>')
def download_photo(photo_id):
    conn = sqlite3.connect('photographer.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM photos WHERE id = ?", (photo_id,))
    photo = c.fetchone()
    conn.close()
    
    if not photo:
        return "Photo not found", 404
    
    if photo['approved'] != 1:
        return "Photo not approved for download", 403
    
    return send_file(photo['original_path'], as_attachment=True, download_name=photo['filename'])

@app.route('/download_all/<token>')
def download_all(token):
    """Download all approved photos as a ZIP file"""
    try:
        conn = sqlite3.connect('photographer.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get session
        c.execute("SELECT * FROM sessions WHERE access_token = ?", (token,))
        session = c.fetchone()
        
        if not session:
            conn.close()
            print(f"ERROR: Invalid token: {token}")
            return "Invalid access link", 404
        
        session_id = session['id']
        print(f"INFO: Download request for session {session_id} - {session['session_name']}")
        
        # Check if ZIP already exists
        if session['zip_path']:
            print(f"INFO: Checking for existing ZIP: {session['zip_path']}")
            if os.path.exists(session['zip_path']):
                # Use existing ZIP
                conn.close()
                zip_filename = os.path.basename(session['zip_path'])
                file_size_mb = os.path.getsize(session['zip_path']) / (1024 * 1024)
                print(f"SUCCESS: Sending existing ZIP: {zip_filename} ({file_size_mb:.1f} MB)")
                return send_file(
                    session['zip_path'],
                    mimetype='application/zip',
                    as_attachment=True,
                    download_name=zip_filename
                )
            else:
                print(f"WARNING: ZIP path in database but file not found: {session['zip_path']}")
        
        # Get all approved photos
        c.execute("SELECT * FROM photos WHERE session_id = ? AND approved = 1", (session_id,))
        photos = c.fetchall()
        
        if not photos:
            conn.close()
            print(f"ERROR: No approved photos for session {session_id}")
            flash('No approved photos available for download', 'warning')
            return redirect(url_for('customer_view', token=token))
        
        print(f"INFO: Found {len(photos)} approved photos. Generating new ZIP...")
        conn.close()
        
        # Generate new ZIP
        zip_path = generate_session_zip(session_id)
        
        if not zip_path:
            print(f"ERROR: generate_session_zip returned None for session {session_id}")
            flash('Error generating download file. Please try again or contact the photographer.', 'error')
            return redirect(url_for('customer_view', token=token))
        
        if not os.path.exists(zip_path):
            print(f"ERROR: ZIP file not found after generation: {zip_path}")
            flash('Error: Download file was not created. Please contact the photographer.', 'error')
            return redirect(url_for('customer_view', token=token))
        
        zip_filename = os.path.basename(zip_path)
        file_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"SUCCESS: Sending newly generated ZIP: {zip_filename} ({file_size_mb:.1f} MB)")
        
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        print(f"EXCEPTION in download_all: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('An unexpected error occurred. Please contact the photographer.', 'error')
        return redirect(url_for('customer_view', token=token))

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['WATERMARK_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
    
    # Initialize database
    init_db()
    
    # Run app
    app.run(debug=True, host='0.0.0.0', port=5000)
