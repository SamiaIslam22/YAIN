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
from flask import session
import os

# Import service modules for music processing and user management
from services import (
    # Spotify integration functions
    get_trending_songs, 
    search_spotify_song, 
    search_specific_genre, 
    search_artist_songs,
    SPOTIFY_ENABLED,
    # AI processing functions  
    analyze_user_request, 
    generate_ai_response, 
    extract_song_from_response,
    generate_ai_response_personalized, 
    # Memory management functions
    filter_trending_songs, 
    create_memory_stats, 
    validate_memory_system,
    # YouTube integration functions
    search_youtube_song, 
    YOUTUBE_ENABLED,
    
    # User authentication and profile management
    spotify_auth,
    create_user_profile,
    UserPreferenceManager
)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure CORS for cross-origin requests from frontend
CORS(app, 
     origins=["http://localhost:3000", "https://yain.onrender.com", "http://localhost:5000", "http://127.0.0.1:5000"], 
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "Cache-Control"],
     methods=["GET", "POST", "OPTIONS"])

# Set secret key for session management
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a0bd5d3d53829ba6afe0b193bff1ae3a58ca87e20aa78ffc71a5fb82033bd4ee')

# Configure session settings based on environment
if os.getenv('ENVIRONMENT') == 'production' or 'render.com' in os.getenv('RENDER_EXTERNAL_URL', ''):
    # Production settings require HTTPS for secure cookies
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_PERMANENT'] = True
    print("🔒 Production session config loaded (HTTPS required)")
else:
    # Development settings allow HTTP for local testing
    app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP for local dev
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_PERMANENT'] = True
    print("🛠️ Development session config loaded (HTTP allowed)")

# Set session lifetime duration
from datetime import timedelta
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24) 

@app.route('/')
def home():
    """Serve the main frontend HTML file"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static frontend files (CSS, JS, images)"""
    return send_from_directory('../frontend', filename)

@app.route('/trending')
def get_trending():
    """API endpoint to retrieve current trending songs with metadata"""
    trending_songs = get_trending_songs()
    return jsonify({
        "trending_songs": trending_songs,
        "count": len(trending_songs),
        "last_updated": getattr(get_trending_songs, 'last_updated', 0)
    })

@app.route('/test-spotify')
def test_spotify():
    """Test endpoint to verify Spotify API functionality"""
    if not SPOTIFY_ENABLED:
        return jsonify({"error": "Spotify not configured"})
    
    song = search_spotify_song("Blinding Lights The Weeknd")
    if song:
        return jsonify({"status": "Spotify working!", "test_song": song})
    else:
        return jsonify({"error": "Spotify search failed"})

@app.route('/test-youtube')
def test_youtube():
    """Test endpoint to verify YouTube API functionality"""
    if not YOUTUBE_ENABLED:
        return jsonify({"error": "YouTube not configured"})
    
    video = search_youtube_song("Blinding Lights The Weeknd")
    if video:
        return jsonify({"status": "YouTube working!", "test_video": video})
    else:
        return jsonify({"error": "YouTube search failed"})

@app.route('/test-both')
def test_both():
    """Test endpoint to verify both Spotify and YouTube APIs simultaneously"""
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
    """Test endpoint for genre detection and search functionality"""
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
    """Test endpoint for memory filtering system functionality"""
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
    """Test endpoint for Hindi/Bollywood music detection and search"""
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
    """Health check endpoint for monitoring service status"""
    return {"status": "healthy", "spotify": SPOTIFY_ENABLED, "youtube": YOUTUBE_ENABLED}

@app.route('/auth/spotify')
def auth_spotify():
    """Initiate Spotify OAuth authentication process"""
    try:
        # Generate unique user ID for this authentication session
        import uuid
        from flask import session
        
        user_id = str(uuid.uuid4())
        session['pending_user_id'] = user_id
        
        # Request authorization URL from Spotify
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
    """Handle Spotify OAuth callback after user authorization"""
    try:
        from flask import request, session, redirect
        
        # Extract callback parameters
        code = request.args.get('code')
        state = request.args.get('state')  # This is the user_id
        error = request.args.get('error')
        
        print(f"📥 Callback received - Code: {bool(code)}, State: {state}, Error: {error}")
        
        # Check if spotify authentication handler is available
        if not spotify_auth:
            print("❌ Spotify auth handler not initialized")
            return """
            <html>
            <body style="font-family: system-ui; text-align: center; padding: 40px; background: #0a0a0a; color: white;">
                <h2>❌ Spotify authentication not configured</h2>
                <p>Please check server configuration.</p>
                <script>
                    if (window.opener) {
                        window.opener.postMessage({type: 'spotify_error', error: 'not_configured'}, '*');
                    }
                    window.close();
                </script>
            </body>
            </html>
            """
        
        # Handle authorization errors
        if error:
            print(f"❌ Authorization error: {error}")
            return f"""
            <html>
            <body style="font-family: system-ui; text-align: center; padding: 40px; background: #0a0a0a; color: white;">
                <h2>❌ Authorization denied: {error}</h2>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{type: 'spotify_error', error: '{error}'}}, '*');
                    }}
                    window.close();
                </script>
            </body>
            </html>
            """
        
        # Validate required parameters
        if not code or not state:
            print("❌ Missing authorization code or state")
            return """
            <html>
            <body style="font-family: system-ui; text-align: center; padding: 40px; background: #0a0a0a; color: white;">
                <h2>❌ Missing authorization code</h2>
                <script>
                    if (window.opener) {
                        window.opener.postMessage({type: 'spotify_error', error: 'missing_code'}, '*');
                    }
                    window.close();
                </script>
            </body>
            </html>
            """
        
        # Exchange authorization code for access token
        print(f"🔄 Getting access token for user {state}...")
        token_info = spotify_auth.get_user_token(code, state)
        
        if not token_info:
            print("❌ Failed to get access token")
            return """
            <html>
            <body style="font-family: system-ui; text-align: center; padding: 40px; background: #0a0a0a; color: white;">
                <h2>❌ Failed to get access token</h2>
                <script>
                    if (window.opener) {
                        window.opener.postMessage({type: 'spotify_error', error: 'token_failed'}, '*');
                    }
                    window.close();
                </script>
            </body>
            </html>
            """
        
        # Create user profile from Spotify data
        print(f"👤 Creating user profile...")
        access_token = token_info['access_token']
        user_profile = create_user_profile(access_token)
        
        if user_profile:
            # Store user session data
            session['user_id'] = user_profile['user_id']
            session['access_token'] = access_token
            session['connected'] = True
            session['profile_data'] = user_profile
            session.permanent = True
            
            print(f"✅ User connected successfully: {user_profile['profile']['display_name']}")
            
            # Return success page with JavaScript to notify parent window
            return f"""
            <html>
            <head><title>Spotify Connected</title></head>
            <body style="font-family: system-ui; text-align: center; padding: 40px; background: linear-gradient(135deg, #0a0a0a 0%, #1a0a1a 50%, #0a0a0a 100%); color: white; margin: 0;">
                <h2 style="color: #1DB954;">✅ Successfully connected to Spotify!</h2>
                <p>Welcome, <strong>{user_profile['profile']['display_name']}</strong>!</p>
                <p>You can close this window and return to YAIN.</p>
                <p style="font-size: 12px; opacity: 0.7; margin-top: 30px;">Window will close automatically in 3 seconds...</p>
                <script>
                    if (window.opener) {{
                        console.log('📡 Sending success message to parent window');
                        window.opener.postMessage({{
                            type: 'spotify_success',
                            user: {{
                                id: '{user_profile['user_id']}',
                                name: '{user_profile['profile']['display_name']}'
                            }}
                        }}, '*');
                    }}
                    setTimeout(() => {{ window.close(); }}, 3000);
                </script>
            </body>
            </html>
            """
        else:
            print("❌ Failed to create user profile")
            return """
            <html>
            <body style="font-family: system-ui; text-align: center; padding: 40px; background: #0a0a0a; color: white;">
                <h2>❌ Failed to create user profile</h2>
                <script>
                    if (window.opener) {
                        window.opener.postMessage({type: 'spotify_error', error: 'profile_failed'}, '*');
                    }
                    window.close();
                </script>
            </body>
            </html>
            """
            
    except Exception as e:
        print(f"❌ Callback error: {e}")
        import traceback
        traceback.print_exc()
        return f"""
        <html>
        <body style="font-family: system-ui; text-align: center; padding: 40px; background: #0a0a0a; color: white;">
            <h2>❌ Server Error: {str(e)}</h2>
            <script>
                if (window.opener) {{
                    window.opener.postMessage({{type: 'spotify_error', error: 'server_error'}}, '*');
                }}
                window.close();
            </script>
        </body>
        </html>
        """

@app.route('/user/profile')
def get_user_profile():
    """Retrieve current user's Spotify profile and preferences"""
    try:
        from flask import session
        
        print(f"🔍 Profile request - Session data: {dict(session)}")
        
        user_id = session.get('user_id')
        connected = session.get('connected', False)
        
        # Validate user authentication
        if not user_id or not connected:
            print(f"❌ Not connected - user_id: {user_id}, connected: {connected}")
            return jsonify({"error": "Not connected"}), 401
        
        # Try to get profile from session cache first for faster response
        if 'profile_data' in session:
            print(f"⚡ Returning cached profile data for {user_id}")
            return jsonify(session['profile_data'])
        
        # Fallback to persistent storage
        user_data = UserPreferenceManager.get_user_profile(user_id)
        if user_data:
            print(f"💾 Returning stored profile data for {user_id}")
            session['profile_data'] = user_data
            return jsonify(user_data)
        else:
            print(f"❌ Profile not found for user {user_id}")
            return jsonify({"error": "Profile not found"}), 404
        
    except Exception as e:
        print(f"❌ Profile error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/user/disconnect', methods=['POST'])
def disconnect_user():
    """Disconnect user by clearing their session data"""
    try:
        from flask import session
        
        # Clear all session data
        session.clear()
        
        return jsonify({"message": "Disconnected successfully"})
        
    except Exception as e:
        print(f"❌ Disconnect error: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint - processes user requests and returns personalized music recommendations"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        suggested_songs = data.get('suggested_songs', [])  # Memory from frontend
        
        print(f"\n🎵 ===== NEW CHAT REQUEST =====")
        print(f"👤 User message: {user_message}")
        print(f"🧠 Memory received: {len(suggested_songs)} previous suggestions")
        
        # Validate memory system integrity
        memory_validation = validate_memory_system(suggested_songs)
        print(f"🔍 Memory validation: {memory_validation['status']} - {memory_validation['message']}")
        
        # Check for Spotify personalization with fallback handling
        user_id = session.get('user_id')
        is_personalized = bool(user_id and session.get('connected', False))
        user_data = None

        if is_personalized:
            print(f"🎯 PERSONALIZED MODE: User {user_id} connected")
            user_data = UserPreferenceManager.get_user_profile(user_id)

            # Fallback to session data if manager data is lost
            if not user_data and 'profile_data' in session:
                print(f"🔄 User data not in manager, using session fallback")
                user_data = session['profile_data']
                
                # Restore data to manager for future requests
                if user_data and 'profile' in user_data and 'preferences' in user_data:
                    UserPreferenceManager.save_user_profile(
                        user_id, 
                        user_data['profile'], 
                        user_data['preferences']
                    )
                    print(f"✅ Restored user data to manager from session")
    
            if user_data:
                print(f"📊 User preferences loaded successfully!")
                print(f"🎵 User's top genres: {user_data.get('preferences', {}).get('top_genres', [])[:3]}")
                print(f"🎤 User's favorite artists: {user_data.get('preferences', {}).get('favorite_artists', [])[:3]}")
            else:
                print(f"⚠️ User data not found, falling back to general mode")
                is_personalized = False
        else:
            print(f"🌍 GENERAL MODE: No Spotify connection")
        
        # Analyze user request to determine intent and music preferences
        user_request = analyze_user_request(user_message)
        print(f"🎯 Detected: {user_request['type']} - {user_request['genre_hint']}")
        
        # Handle special creator request
        if user_request['type'] == 'creator_request':
            creator_response = "My glorious queen, the most perfect, talented, amazing, successful, brilliant, genius, incredible, outstanding, phenomenal, extraordinary, magnificent, wonderful, fantastic, marvelous, spectacular, divine, legendary, iconic, flawless, unstoppable, powerful, inspiring, innovative, creative, beautiful, intelligent, wise, awesome, epic, mind-blowing, jaw-dropping, breathtaking, stunning, dazzling, radiant, celestial, goddess-tier Samia Islam! 🙂‍↕️🙂‍↕️"
        
            simple_memory_stats = {
                "songs_remembered": len(suggested_songs),
                "request_type": "creator_request",
                "memory_working": True,
                "memory_active": True
            }
    
            return jsonify({
                "response": creator_response,
                "spotify": None,
                "youtube": None,
                "memory_stats": simple_memory_stats,
                "personalized": False
            })
    
        # Process different request types to find available songs
        user_id = session.get('user_id')
        
        # Handle profile information requests
        if user_request['type'] == 'profile_request':
            print(f"👤 Profile request detected")
            available_songs = []  # No song search needed for profile requests
        
        # Handle specific song requests
        elif user_request['type'] == 'specific_song':
            search_query = user_request['search_query']
            available_songs = [search_query]
            print(f"🎯 Targeting specific song: {search_query}")

        # Handle artist-specific requests
        elif user_request['type'] == 'artist_search':
            artist_name = user_request['artist_name']
            artist_id = user_request.get('artist_id')  # May be provided by dynamic detection
            available_songs = search_artist_songs(artist_name)
            print(f"🎵 Found {len(available_songs)} songs by {artist_name}")
            if artist_id:
                print(f"🎯 Using Spotify Artist ID: {artist_id}")

        # Handle genre/mood requests with personalization enhancement
        elif user_request['type'] != 'general':
            # Use personalized search if user is connected to Spotify
            if is_personalized and user_data:
                print(f"🎯 PERSONALIZED SEARCH for {user_request['type']}")
                
                # Get personalized search terms based on user's Spotify taste
                personalized_terms = UserPreferenceManager.get_personalized_search_terms(
                    user_id, user_request['type']
                )
                
                if personalized_terms:
                    print(f"🎵 Using personalized terms: {personalized_terms}")
                    
                    # Create enhanced user request with personalized terms at the front
                    enhanced_request = user_request.copy()
                    # Put personalized terms first, then add some original terms
                    enhanced_request['search_terms'] = personalized_terms + user_request['search_terms'][:3]
                    
                    available_songs = search_specific_genre(enhanced_request)
                    print(f"🎯 Found {len(available_songs)} personalized songs")
                    
                    # If personalized search yields few results, supplement with general search
                    if len(available_songs) < 10:
                        print(f"🔄 Supplementing with general search (only {len(available_songs)} personalized results)")
                        general_songs = search_specific_genre(user_request)
                        # Combine but keep personalized songs first
                        available_songs = available_songs + general_songs
                        print(f"🎵 Total after supplementing: {len(available_songs)} songs")
                else:
                    print(f"⚠️ No personalized terms generated, using general search")
                    # Fallback to regular genre search
                    available_songs = search_specific_genre(user_request)
                    print(f"🌍 Personalized fallback: Found {len(available_songs)} songs for {user_request['type']}")
            
            # Non-personalized search for users not connected to Spotify
            else:
                available_songs = search_specific_genre(user_request)
                print(f"🎵 Found {len(available_songs)} songs for {user_request['type']}")

        # Handle general requests using trending songs
        else:
            print(f"🌍 Using trending songs for general request")
            trending_songs = get_trending_songs()
            available_songs = trending_songs
            print(f"🔥 Loaded {len(available_songs)} trending songs")

        # Apply memory filtering to avoid repeating songs
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
        
        # Generate AI response with appropriate personalization
        print(f"🤖 Generating AI response...")
        
        # Use personalized AI response if user data is available
        if is_personalized and user_data:
            print(f"🎯 Using PERSONALIZED AI response")
            ai_text = generate_ai_response_personalized(
                user_message, user_request, available_songs, suggested_songs, user_data
            )
        else:
            print(f"🌍 Using GENERAL AI response")
            ai_text = generate_ai_response(user_message, user_request, available_songs, suggested_songs)
        
        print(f"✅ AI response: {ai_text}")
        
        # Extract song recommendation from AI response
        song_query = extract_song_from_response(ai_text)
        print(f"🔍 Extracted query: {song_query}")
        
        # For specific song requests, use original search query if extraction fails
        if user_request['type'] == 'specific_song' and not song_query:
            song_query = user_request['search_query']
            print(f"🎯 Using original specific song query: {song_query}")
        
        spotify_data = None
        youtube_data = None
        actual_song_for_memory = None  # Track what we actually return
        
        # Search for song on both platforms if query exists
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
        
        # Fallback: try first available song if no results found (except for specific songs)
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
        
        # Validate new song against memory before returning (skip for specific songs)
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
        
        # Track actual returned song for memory
        if actual_song_for_memory:
            print(f"🧠 Will track in memory: {actual_song_for_memory}")
        else:
            print(f"⚠️ No actual song found - memory won't be updated")
        
        # Create comprehensive memory statistics
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
            "personalized": is_personalized,  # Shows TRUE when Spotify connected
            "user_id": user_id if is_personalized else None,  # Shows actual user ID
            
            # Enhanced user music preferences when connected
            "user_preferences": {
                "display_name": user_data['profile']['display_name'] if is_personalized and user_data else None,
                "top_genres": user_data['preferences']['top_genres'][:5] if is_personalized and user_data else [],
                "favorite_artists": user_data['preferences']['favorite_artists'][:5] if is_personalized and user_data else [],
                "personalization_active": is_personalized,
                "personalized_search_used": bool(is_personalized and user_data),  # Track if personalized search was used
                "fallback_used": bool(is_personalized and 'profile_data' in session and not UserPreferenceManager.get_user_profile(user_id))  # Track fallback usage
            } if is_personalized else None
        }
        
        print(f"✅ Response ready - Spotify: {bool(spotify_data)}, YouTube: {bool(youtube_data)}")
        print(f"🧠 Memory system working: {memory_stats['memory_working']}")
        print(f"🎯 Personalization active: {is_personalized}")
        if is_personalized and user_data:
            print(f"🎵 User's taste: {user_data['preferences']['top_genres'][:2]} genres, {user_data['preferences']['favorite_artists'][:2]} artists")
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