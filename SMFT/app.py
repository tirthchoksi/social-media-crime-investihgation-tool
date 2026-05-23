import os
import socket  # For Chain of Custody (Device Name)
from datetime import datetime # For Chain of Custody (Time)
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

# --- IMPORT MODULES ---
from modules.metadata import get_exif_data
from modules.analysis import scan_text_for_crime
from modules.hashing import calculate_hash

# Scrapers
from modules.scraper_selenium import download_latest_posts_selenium as download_latest_posts
from modules.scraper_twitter import scrape_twitter_profile  # <--- NEW TWITTER IMPORT
from modules.scraper_facebook import scrape_facebook_profile
# OCR (Optical Character Recognition)
try:
    from modules.ocr import extract_text_from_image
except ImportError:
    extract_text_from_image = None

app = Flask(__name__)

# Config
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

# --- IMAGE ANALYSIS ROUTE ---
@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    if 'file' not in request.files: return redirect(request.url)
    file = request.files['file']
    if file.filename == '': return redirect(request.url)

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 1. Forensic Hash & Metadata
        file_hash = calculate_hash(filepath)
        metadata = get_exif_data(filepath)
        
        # 2. OCR Fallback (if no metadata found)
        if "Status" in metadata or len(metadata) < 2:
            if extract_text_from_image:
                ocr_text = extract_text_from_image(filepath)
                if ocr_text:
                    crime_results = scan_text_for_crime(ocr_text)
                    metadata["[FORENSIC NOTE]"] = "Metadata scrubbed. Performed OCR."
                    metadata["[EXTRACTED TEXT]"] = ocr_text[:200] + "..."
                    if crime_results:
                        for c, k in crime_results.items():
                            metadata[f"[ALERT: {c.upper()}]"] = ", ".join(k)

        return render_template('report.html', evidence_type="Image Forensics", target=filename, hash_val=file_hash, data=metadata)

# --- TEXT ANALYSIS ROUTE ---
@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    text_input = request.form['text_content']
    results = scan_text_for_crime(text_input)
    
    formatted = {}
    if results:
        for k, v in results.items(): formatted[k.upper()] = ", ".join(v)
    
    return render_template('report.html', evidence_type="Text Analysis", target="Manual Input", hash_val="N/A", data=formatted)

# --- INSTAGRAM PROFILE ROUTE ---
@app.route('/analyze_profile', methods=['POST'])
def analyze_profile():
    profile_link = request.form['profile_link']
    
    # 1. Clean Username
    temp_user = profile_link
    if "instagram.com" in temp_user:
        temp_user = temp_user.split("instagram.com/")[-1]
    username = temp_user.split("?")[0].replace("/", "").replace('"', '').replace("'", "").rstrip('.')
    
    print(f"Analyzing Instagram: '{username}'")
    
    # 2. Run Scraper
    posts = download_latest_posts(username, limit=3)
    
    if not posts:
        return render_template('report.html', 
                             evidence_type="Profile Analysis Failed", 
                             target=username, 
                             hash_val="Error", 
                             data={"Error": "Could not scrape profile. Is it private?"})

    full_report = {}
    
    # Chain of Custody Info
    device_name = socket.gethostname() 
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. Analyze Results
    for i, post in enumerate(posts):
        image_path = post.get('image_path')
        post_comments = post.get('comments', [])
        date = post.get('date', 'Unknown')
        
        # Log Chain of Custody
        full_report[f" > [CHAIN OF CUSTODY] Post {i+1}"] = f"Device: {device_name} | Time: {scan_time}"
        
        post_key = f"POST #{i+1} ({date})"
        full_report[post_key] = f"CAPTION: {post.get('caption', '')[:100]}..."

        # Caption Scan
        caption_crime = scan_text_for_crime(post.get('caption', ''))
        if caption_crime:
             full_report[f" > [ALERT] Caption Threat"] = str(caption_crime)

        # Image Hash & OCR
        if image_path:
            try:
                img_hash = calculate_hash(image_path)
                full_report[f" > [HASH] Integrity"] = img_hash
            except: pass

            if extract_text_from_image:
                ocr_text = extract_text_from_image(image_path)
                if ocr_text:
                    ocr_crime = scan_text_for_crime(ocr_text)
                    if ocr_crime:
                        full_report[f" > [ALERT] Hidden Text"] = str(ocr_crime)
        else:
             full_report[f" > [INFO] Post {i+1}"] = "Video/Reel (No Image Analysis)"

        # Comment Analysis
        if post_comments:
            suspicious_count = 0
            for comment in post_comments:
                crime_found = scan_text_for_crime(comment)
                if crime_found:
                    full_report[f" > [ALERT] Suspicious Comment"] = f"'{comment}' -> {str(crime_found)}"
                    suspicious_count += 1
            
            if suspicious_count == 0:
                 comment_preview = " | ".join(post_comments[:3]) 
                 full_report[f" > [COMMENTS] Post {i+1}"] = f"Scanned {len(post_comments)} comments. Clean. (Sample: {comment_preview}...)"
        else:
            full_report[f" > [COMMENTS] Post {i+1}"] = "0 Comments found."

    return render_template('report.html', 
                         evidence_type=f"Instagram Profile: {username}", 
                         target=profile_link, 
                         hash_val="Multiple Files Scanned", 
                         data=full_report)

# --- TWITTER (X) PROFILE ROUTE ---
@app.route('/analyze_twitter', methods=['POST'])
def analyze_twitter():
    handle = request.form['twitter_handle']
    print(f"Analyzing Twitter: @{handle}")

    # 1. Run Scraper
    tweets = scrape_twitter_profile(handle, limit=5)
    
    if not tweets:
        return render_template('report.html', evidence_type="X Analysis Failed", target=handle, hash_val="Error", data={"Error": "Could not scrape tweets. Login required?"})

    report_data = {}
    for i, tweet in enumerate(tweets):
        key = f"TWEET #{i+1} ({tweet.get('date', 'Unknown')})"
        report_data[key] = tweet.get('text', 'No Text')
        
        # Scan text
        crime = scan_text_for_crime(tweet.get('text', ''))
        if crime:
            report_data[f" > [ALERT] Tweet {i+1}"] = str(crime)
            
    return render_template('report.html', evidence_type="X (Twitter) Analysis", target=handle, hash_val="Text Analysis", data=report_data)
# --- FACEBOOK PROFILE ROUTE ---
@app.route('/analyze_facebook', methods=['POST'])
def analyze_facebook():
    page_name = request.form['facebook_handle']
    print(f"Analyzing Facebook: {page_name}")

    # 1. Run the NEW Deep Scraper
    posts = scrape_facebook_profile(page_name, limit=5)
    
    if not posts:
        return render_template('report.html', 
                             evidence_type="Facebook Analysis Failed", 
                             target=page_name, 
                             hash_val="Error", 
                             data={"Error": "Could not scrape page. Check login or privacy settings."})

    report_data = {}
    
    # 2. Analyze the Data
    for i, post in enumerate(posts):
        # Check if this is the "Profile Metadata" we saved earlier
        if "PROFILE METADATA" in post['text']:
             key = "ACCOUNT INFO"
             content = post['text']
        else:
             key = f"POST #{i} ({post['date']})"
             content = post['text']

        report_data[key] = content
        
        # Scan for crime only in real posts
        if "PROFILE METADATA" not in post['text']:
            crime = scan_text_for_crime(post['text'])
            if crime:
                report_data[f" > [ALERT] Post {i}"] = str(crime)
            
    return render_template('report.html', evidence_type="Facebook Page Analysis", target=page_name, hash_val="Text/Profile Analysis", data=report_data)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)