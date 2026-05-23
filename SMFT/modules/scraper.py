import instaloader
import os
import glob
import time
import shutil

def download_latest_posts(target_username, limit=1):
    """
    Downloads the last few posts from a public Instagram profile.
    Returns a list of dictionaries with image paths and captions.
    """
    # Create a unique download folder
    download_folder = f"downloads_{target_username}"
    
    # Initialize Instaloader
    L = instaloader.Instaloader(
        download_pictures=True,
        download_videos=False, 
        download_video_thumbnails=False,
        download_geotags=False, 
        download_comments=False,
        save_metadata=False,
        compress_json=False
    )

    # --- 🟢 ANTI-BLOCK LOGIN (OPTIONAL BUT RECOMMENDED) ---
    # If you get "HTTP 429" errors, fill these in with a DUMMY account.
    # If you leave them empty, it will try to scrape anonymously (lower limits).
    MY_USER = ""  # Put dummy username inside quotes, e.g. "forensic_student_01"
    MY_PASS = ""  # Put dummy password inside quotes
    
    if MY_USER and MY_PASS:
        try:
            print(f"[*] Logging in as {MY_USER} to avoid 429 errors...")
            L.login(MY_USER, MY_PASS)
            print("[*] Login successful!")
        except Exception as e:
            print(f"[!] Login failed: {e}")
            print("[!] Attempting anonymous scrape (might get blocked)...")
    # -----------------------------------------------------

    posts_data = []

    try:
        print(f"[*] Connecting to profile: {target_username}...")
        
        # Load Profile safely
        try:
            profile = instaloader.Profile.from_username(L.context, target_username)
        except Exception as e:
            print(f"Profile Error: {e}")
            return []

        # Check if private
        if profile.is_private:
            # If we are logged in, we might be able to see it IF we follow them.
            # Otherwise, we can't scrape it.
            if not L.context.is_logged_in:
                print(f"Error: Account {target_username} is PRIVATE.")
                return [] 

        count = 0
        posts = profile.get_posts()

        for post in posts:
            if count >= limit:
                break
            
            print(f"Downloading post {count+1}...")
            
            try:
                # Download the post to the folder
                L.download_post(post, target=download_folder)
            except Exception as e:
                print(f"Skipping post due to download error: {e}")
                continue
            
            # Find the .jpg file we just downloaded using glob (safer)
            list_of_files = glob.glob(f'{download_folder}/*.jpg')
            
            if list_of_files:
                # Get the most recent file in the folder
                latest_file = max(list_of_files, key=os.path.getctime)
                
                # --- CRITICAL FIX: KEY IS 'image_path' ---
                post_info = {
                    "image_path": latest_file, 
                    "caption": post.caption if post.caption else "No Caption",
                    "date": str(post.date_utc)
                }
                posts_data.append(post_info)
                # -----------------------------------------
            else:
                print(f"Warning: No image found for post {count+1} (might be a video).")
                
            count += 1
            # Sleep to avoid getting blocked (Essential for 429 prevention)
            time.sleep(5) 
            
        return posts_data

    except Exception as e:
        print(f"Error scraping profile: {e}")
        return []