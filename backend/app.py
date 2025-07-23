# ------------------------------------------------------------
# © 2025 Samia Islam. All rights reserved.
# This file is part of the "YAIN" project.
# Released under CC BY-NC 4.0 license.
# For demo and educational use only — not for commercial use.
# ------------------------------------------------------------

# YAIN Backend Application
# Main Flask app for handling music requests and AI interactions



from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask import send_from_directory
import os

# Import our organized services (NO USER SERVICES)
from services import (
    # Spotify functions
    get_trending_songs, 
    search_spotify_song, 
    search_specific_genre, 
    search_artist_songs,  # ✅ Clean import
    SPOTIFY_ENABLED,
    # AI functions  
    analyze_user_request, 
    generate_ai_response, 
    extract_song_from_response,
    # Memory functions
    filter_trending_songs, 
    create_memory_stats, 
    validate_memory_system,
    # YouTube functions
    search_youtube_song, 
    YOUTUBE_ENABLED,

    spotify_auth,
    create_user_profile,
    UserPreferenceManager
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["*"], supports_credentials=True)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a0bd5d3d53829ba6afe0b193bff1ae3a58ca87e20aa78ffc71a5fb82033bd4ee')

app.config['SESSION_COOKIE_SECURE'] = True  # You're on HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_PERMANENT'] = False


@app.route('/')
def home():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('../frontend', filename)

@app.route('/trending')
def get_trending():
    """Get current trending songs"""
    trending_songs = get_trending_songs()
    return jsonify({
        "trending_songs": trending_songs,
        "count": len(trending_songs),
        "last_updated": getattr(get_trending_songs, 'last_updated', 0)
    })

@app.route('/test-spotify')
def test_spotify():
    """Test if Spotify is working"""
    if not SPOTIFY_ENABLED:
        return jsonify({"error": "Spotify not configured"})
    
    song = search_spotify_song("Blinding Lights The Weeknd")
    if song:
        return jsonify({"status": "Spotify working!", "test_song": song})
    else:
        return jsonify({"error": "Spotify search failed"})

@app.route('/test-youtube')
def test_youtube():
    """Test if YouTube is working"""
    if not YOUTUBE_ENABLED:
        return jsonify({"error": "YouTube not configured"})
    
    video = search_youtube_song("Blinding Lights The Weeknd")
    if video:
        return jsonify({"status": "YouTube working!", "test_video": video})
    else:
        return jsonify({"error": "YouTube search failed"})

@app.route('/test-both')
def test_both():
    """Test both Spotify and YouTube"""
    test_query = "Blinding Lights The Weeknd"
    
    results = {
        "spotify": search_spotify_song(test_query) if SPOTIFY_ENABLED else None,
        "youtube": search_youtube_song(test_query) if YOUTUBE_ENABLED else None
    }
    
    return jsonify({
        "status": "Testing both platforms",
        "results": results
    })

@app.route('/test-genre/<query>')
def test_genre(query):
    """🎯 Test the genre detection system"""
    user_request = analyze_user_request(query)
    songs = search_specific_genre(user_request) if user_request['type'] != 'general' else []
    
    return jsonify({
        "query": query,
        "detected_type": user_request['type'],
        "genre_hint": user_request['genre_hint'],
        "search_terms": user_request['search_terms'],
        "found_songs": songs[:5],  # Show first 5 songs
        "total_found": len(songs)
    })

@app.route('/test-memory')
def test_memory():
    """🧠 Test the memory system"""
    test_suggested = ["September by Earth, Wind & Fire", "Blinding Lights by The Weeknd"]
    trending = get_trending_songs()
    filtered = filter_trending_songs(trending, test_suggested)
    
    return jsonify({
        "status": "Testing memory system",
        "original_trending_count": len(trending),
        "filtered_trending_count": len(filtered),
        "test_suggested_songs": test_suggested,
        "filtered_sample": filtered[:5]
    })

@app.route('/test-hindi')
def test_hindi():
    """🇮🇳 Test Hindi/Bollywood detection and search"""
    test_queries = ["give me some hindi song", "bollywood music", "arijit singh"]
    results = {}
    
    for query in test_queries:
        user_request = analyze_user_request(query)
        songs = search_specific_genre(user_request) if user_request['type'] != 'general' else []
        results[query] = {
            "detected_type": user_request['type'],
            "genre_hint": user_request['genre_hint'],
            "found_songs": songs[:3],
            "total_found": len(songs)
        }
    
    return jsonify({
        "status": "Testing Hindi/Bollywood detection",
        "results": results
    })


@app.route('/health')
def health():
    return {"status": "healthy", "spotify": SPOTIFY_ENABLED, "youtube": YOUTUBE_ENABLED}

# Add these routes to your app.py file (after your test routes, before /chat route)

@app.route('/auth/spotify')
def auth_spotify():
    """Get Spotify authorization URL"""
    try:
        # Generate a unique user ID for this session
        import uuid
        from flask import session
        
        user_id = str(uuid.uuid4())
        session['pending_user_id'] = user_id
        
        # Get auth URL
        auth_url = spotify_auth.get_auth_url(user_id)
        
        if auth_url:
            return jsonify({"auth_url": auth_url})
        else:
            return jsonify({"error": "Failed to create auth URL"}), 500
            
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/callback')
def spotify_callback():
    """Handle Spotify OAuth callback"""
    try:
        from flask import request, session, redirect
        
        code = request.args.get('code')
        state = request.args.get('state')  # This is the user_id
        error = request.args.get('error')
        
        if error:
            return f"<html><body><h2>Authorization denied: {error}</h2><script>window.close();</script></body></html>"
        
        if not code or not state:
            return "<html><body><h2>Missing authorization code</h2><script>window.close();</script></body></html>"
        
        # Get access token
        token_info = spotify_auth.get_user_token(code, state)
        
        if not token_info:
            return "<html><body><h2>Failed to get access token</h2><script>window.close();</script></body></html>"
        
        # Create user profile
        access_token = token_info['access_token']
        user_profile = create_user_profile(access_token)
        
        if user_profile:
            # Store user info in session
            session['user_id'] = user_profile['user_id']
            session['access_token'] = access_token
            session['connected'] = True
            
            print(f"✅ User connected: {user_profile['profile']['display_name']}")
            
            return """
            <html>
            <body>
                <h2>✅ Successfully connected to Spotify!</h2>
                <p>You can close this window and return to YAIN.</p>
                <script>
                    // Notify parent window and close
                    if (window.opener) {
                        window.opener.postMessage('spotify_connected', '*');
                    }
                    window.close();
                </script>
            </body>
            </html>
            """
        else:
            return "<html><body><h2>Failed to create user profile</h2><script>window.close();</script></body></html>"
            
    except Exception as e:
        print(f"❌ Callback error: {e}")
        return f"<html><body><h2>Error: {str(e)}</h2><script>window.close();</script></body></html>"

@app.route('/user/profile')
def get_user_profile():
    """Get current user profile"""
    try:
        from flask import session
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Not connected"}), 401
        
        user_data = UserPreferenceManager.get_user_profile(user_id)
        if user_data:
            return jsonify(user_data)
        else:
            return jsonify({"error": "Profile not found"}), 404
            
    except Exception as e:
        print(f"❌ Profile error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/user/disconnect', methods=['POST'])
def disconnect_user():
    """Disconnect user"""
    try:
        from flask import session
        
        # Clear session
        session.clear()
        
        return jsonify({"message": "Disconnected successfully"})
        
    except Exception as e:
        print(f"❌ Disconnect error: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/chat', methods=['POST'])
def chat():
    """🧠 MAIN CHAT ENDPOINT - NOW WITH SPECIFIC SONG + ARTIST SEARCH!"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        suggested_songs = data.get('suggested_songs', [])  # 🧠 Memory from frontend
        
        print(f"\n🎵 ===== NEW CHAT REQUEST =====")
        print(f"👤 User message: {user_message}")
        print(f"🧠 Memory received: {len(suggested_songs)} previous suggestions")
        
        # 🧠 VALIDATE MEMORY SYSTEM
        memory_validation = validate_memory_system(suggested_songs)
        print(f"🔍 Memory validation: {memory_validation['status']} - {memory_validation['message']}")
        
        # 🌍 GENERAL MODE ONLY - No personalization
        is_personalized = False
        print(f"🌍 General mode (personalization disabled)")
        
        # 🎯 ANALYZE what the user actually wants
        user_request = analyze_user_request(user_message)
        print(f"🎯 Detected: {user_request['type']} - {user_request['genre_hint']}")
        
        # 🎵 HANDLE SPECIFIC SONG SEARCH (NEW!)
        if user_request['type'] == 'specific_song':
            search_query = user_request['search_query']
            available_songs = [search_query]
            print(f"🎯 Targeting specific song: {search_query}")
            
        # 🎤 HANDLE ARTIST SEARCH (NEW!)
        elif user_request['type'] == 'artist_search':
            artist_name = user_request['artist_name']
            artist_id = user_request.get('artist_id')  # May be provided by dynamic detection
            available_songs = search_artist_songs(artist_name)
            print(f"🎵 Found {len(available_songs)} songs by {artist_name}")
            if artist_id:
                print(f"🎯 Using Spotify Artist ID: {artist_id}")
            
        # 🎵 Get songs based on user's specific request
        elif user_request['type'] != 'general':
            # User has a specific genre/mood request - prioritize that!
            available_songs = search_specific_genre(user_request)
            print(f"🎵 Found {len(available_songs)} songs for {user_request['type']}")
        else:
            # General request - use trending songs
            print(f"🌍 Using trending songs for general request")
            trending_songs = get_trending_songs()
            available_songs = trending_songs
            print(f"🔥 Loaded {len(available_songs)} trending songs")
        
        # 🧠 MEMORY: Filter out already suggested songs (UPDATED!)
        original_count = len(available_songs)
        
        if user_request['type'] == 'specific_song':
            filtered_count = original_count  # Don't filter specific songs
            print(f"🎯 Specific song request - skipping memory filter")
        else:
            available_songs = filter_trending_songs(available_songs, suggested_songs)
            filtered_count = len(available_songs)
            print(f"🧠 Memory filter: {original_count} → {filtered_count} songs available")
        
        if filtered_count == 0:
            print(f"⚠️ No songs available after memory filtering!")
        
        # 🤖 Generate AI response
        print(f"🤖 Generating AI response...")
        ai_text = generate_ai_response(user_message, user_request, available_songs, suggested_songs)
        print(f"✅ AI response: {ai_text}")
        
        # 🔍 Extract song and search both platforms
        song_query = extract_song_from_response(ai_text)
        print(f"🔍 Extracted query: {song_query}")
        
        # 🎵 FOR SPECIFIC SONG REQUESTS - use the original search query if extraction fails
        if user_request['type'] == 'specific_song' and not song_query:
            song_query = user_request['search_query']
            print(f"🎯 Using original specific song query: {song_query}")
        
        spotify_data = None
        youtube_data = None
        actual_song_for_memory = None  # 🧠 Track what we actually return
        
        if song_query:
            print(f"🎧 Searching Spotify for: {song_query}")
            if SPOTIFY_ENABLED:
                spotify_data = search_spotify_song(song_query)
                if spotify_data:
                    print(f"✅ Spotify found: {spotify_data['name']} by {spotify_data['artist']} (score: {spotify_data['match_score']:.2f})")
                    actual_song_for_memory = f"'{spotify_data['name']}' by {spotify_data['artist']}"
                else:
                    print(f"❌ Spotify search failed for: {song_query}")
            
            print(f"📺 Searching YouTube for: {song_query}")
            if YOUTUBE_ENABLED:
                youtube_data = search_youtube_song(song_query)
                if youtube_data:
                    print(f"✅ YouTube found: {youtube_data['title']}")
                    # If no Spotify data, use YouTube for memory
                    if not actual_song_for_memory:
                        actual_song_for_memory = f"'{youtube_data['title']}' by {youtube_data['channel']}"
                else:
                    print(f"❌ YouTube search failed for: {song_query}")
        
        # 🧠 FALLBACK: If no song found, try first available song (except for specific songs)
        if not spotify_data and not youtube_data and available_songs and user_request['type'] != 'specific_song':
            print(f"🔄 No song found, trying first available: {available_songs[0]}")
            fallback_query = available_songs[0]
            
            if SPOTIFY_ENABLED:
                spotify_data = search_spotify_song(fallback_query)
                if spotify_data:
                    actual_song_for_memory = f"'{spotify_data['name']}' by {spotify_data['artist']}"
                    print(f"✅ Fallback Spotify: {actual_song_for_memory}")
            
            if YOUTUBE_ENABLED and not youtube_data:
                youtube_data = search_youtube_song(fallback_query)
                if youtube_data and not actual_song_for_memory:
                    actual_song_for_memory = f"'{youtube_data['title']}' by {youtube_data['channel']}"
                    print(f"✅ Fallback YouTube: {actual_song_for_memory}")
        
        # 🧠 CRITICAL: Validate new song against memory before returning (skip for specific songs)
        if actual_song_for_memory and user_request['type'] != 'specific_song':
            memory_check = validate_memory_system(suggested_songs, actual_song_for_memory)
            if not memory_check['valid']:
                print(f"🚨 MEMORY VIOLATION: {memory_check['message']}")
                # Try to find a different song
                if len(available_songs) > 1:
                    for alternative_song in available_songs[1:6]:  # Try next 5 songs
                        alt_spotify = search_spotify_song(alternative_song)
                        if alt_spotify:
                            alt_song_for_memory = f"'{alt_spotify['name']}' by {alt_spotify['artist']}"
                            alt_check = validate_memory_system(suggested_songs, alt_song_for_memory)
                            if alt_check['valid']:
                                spotify_data = alt_spotify
                                actual_song_for_memory = alt_song_for_memory
                                print(f"✅ Found alternative: {actual_song_for_memory}")
                                break
        
        # 🧠 CRITICAL: Track actual returned song for memory
        if actual_song_for_memory:
            print(f"🧠 Will track in memory: {actual_song_for_memory}")
        else:
            print(f"⚠️ No actual song found - memory won't be updated")
        
        # 📊 Create memory statistics
        memory_stats = {
            "songs_remembered": len(suggested_songs),
            "songs_available_before_filter": original_count,
            "songs_available_after_filter": filtered_count,
            "songs_filtered_out": max(0, original_count - filtered_count),
            "request_type": user_request['type'],
            "actual_song_returned": actual_song_for_memory,
            "memory_working": len(suggested_songs) >= 0,
            "memory_active": True,
            "search_successful": bool(spotify_data or youtube_data),
            "validation": memory_validation,
            "filter_effectiveness": (max(0, original_count - filtered_count)) / max(1, original_count) * 100
        }
        
        print(f"📦 Preparing response...")
        response_data = {
            "response": ai_text,
            "song": spotify_data,  # Keep for backwards compatibility
            "spotify": spotify_data,
            "youtube": youtube_data,
            "memory_stats": memory_stats,
            "personalized": False,  # Always false in general mode
            "user_id": None  # Always null in general mode
        }
        
        print(f"✅ Response ready - Spotify: {bool(spotify_data)}, YouTube: {bool(youtube_data)}")
        print(f"🧠 Memory system working: {memory_stats['memory_working']}")
        print(f"🎵 ===== CHAT REQUEST COMPLETE =====\n")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ ERROR in chat(): {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "response": "Sorry, I had trouble processing your request!",
            "spotify": None,
            "youtube": None,
            "memory_stats": {
                "error": True,
                "message": "Request failed",
                "memory_working": False,
                "memory_active": False
            }
        }), 500
        
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)