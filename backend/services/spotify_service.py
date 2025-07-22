# ------------------------------------------------------------
# © 2025 Samia Islam. All rights reserved.
# This file is part of the "YAIN" project.
# Released under CC BY-NC 4.0 license.
# For demo and educational use only — not for commercial use.
# ------------------------------------------------------------

# Spotify Service Module
# Provides functions to interact with Spotify API for song searches, trending songs, and genre-specific searches
# Handles caching and optimizations for performance


import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import time
import random
import re
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed

# Enhanced cache for better performance
trending_cache = {
    'songs': [],
    'last_updated': 0,
    'cache_duration': 3600  # 1 hour cache
}

# NEW: Search result cache to avoid repeated API calls
search_cache = {}
cache_ttl = 1800  # 30 minutes

# Configure Spotify
def init_spotify():
    """Initialize Spotify client"""
    try:
        spotify_credentials = SpotifyClientCredentials(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
        )
        spotify = spotipy.Spotify(client_credentials_manager=spotify_credentials)
        return spotify, True
    except:
        print("⚠️  Spotify credentials not found")
        return None, False

# Initialize on import
spotify, SPOTIFY_ENABLED = init_spotify()

def search_spotify_song(query):
    """🚀 OPTIMIZED: Fast Spotify search with caching and reduced API calls"""
    if not SPOTIFY_ENABLED:
        return None
    
    print(f"\n🔍 === FAST SPOTIFY SEARCH ===")
    print(f"🎵 Query: {query}")
    
    # Check cache first
    cache_key = query.lower().strip()
    current_time = time.time()
    
    if cache_key in search_cache:
        cached_result, cached_time = search_cache[cache_key]
        if current_time - cached_time < cache_ttl:
            print(f"⚡ Cache hit! Returning cached result for: {query}")
            return cached_result
    
    try:
        # Parse the query to extract song and artist
        song_name, artist_name = extract_song_and_artist(query)
        
        if not song_name or not artist_name:
            print(f"❌ Could not parse song and artist from query")
            return None
        
        print(f"🎯 Searching for: '{song_name}' by '{artist_name}'")
        
        # 🚀 OPTIMIZED: Only use 2 best strategies instead of 4
        search_strategies = [
            f'track:"{song_name}" artist:"{artist_name}"',  # Most accurate
            f'"{song_name}" "{artist_name}"'                # Fallback
        ]
        
        best_match = None
        best_score = 0.0
        
        for i, strategy in enumerate(search_strategies, 1):
            print(f"🔍 Strategy {i}/2: {strategy}")
            
            try:
                # 🚀 SINGLE market search instead of multiple markets
                results = spotify.search(q=strategy, type='track', limit=5, market='US')
                tracks = results['tracks']['items']
                
                if not tracks:
                    print(f"  ❌ No results")
                    continue
                
                print(f"  📊 Found {len(tracks)} results")
                
                # Score only top 3 results for speed
                for j, track in enumerate(tracks[:3]):
                    if not track:
                        continue
                        
                    score = calculate_match_score(
                        song_name, artist_name,
                        track['name'], track['artists'][0]['name']
                    )
                    
                    print(f"  🎵 {track['name']} by {track['artists'][0]['name']} (score: {score:.2f})")
                    
                    if score > best_score:
                        best_score = score
                        best_match = track
                        print(f"  ⭐ NEW BEST! Score: {score:.2f}")
                
                # 🚀 EARLY EXIT: If we found a good match (80%+), stop searching
                if best_score >= 0.8:
                    print(f"🎯 Great match found (score: {best_score:.2f}), stopping early")
                    break
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue
        
        # Process result
        result = None
        if best_match and best_score >= 0.6:
            result = {
                'name': best_match['name'],
                'artist': best_match['artists'][0]['name'],
                'album': best_match['album']['name'],
                'preview_url': best_match['preview_url'],
                'spotify_url': best_match['external_urls']['spotify'],
                'image_url': best_match['album']['images'][0]['url'] if best_match['album']['images'] else None,
                'popularity': best_match['popularity'],
                'match_score': best_score
            }
            
            print(f"✅ Found: '{result['name']}' by {result['artist']} (score: {best_score:.2f})")
        else:
            print(f"❌ No good match found (best score: {best_score:.2f})")
        
        # Cache the result (even if None)
        search_cache[cache_key] = (result, current_time)
        
        return result
                
    except Exception as e:
        print(f"❌ Spotify search error: {e}")
        return None

def search_specific_genre_optimized(genre_info):
    """🚀 OPTIMIZED: Faster genre search with reduced API calls"""
    if not SPOTIFY_ENABLED:
        return []
    
    found_songs = []
    genre_type = genre_info['type']
    
    # 🚀 REDUCED: Use only top 8 search terms instead of 20+
    search_terms = genre_info['search_terms'][:8]
    
    # 🚀 OPTIMIZED: Choose best markets for each genre
    if genre_type == 'bengali':
        markets = ['IN', 'US']  # Reduced from 3 to 2
    elif genre_type in ['tamil', 'telugu', 'punjabi', 'hindi_bollywood']:
        markets = ['IN', 'US']
    elif genre_type == 'afrobeats':
        markets = ['NG', 'US']  # Reduced from 6 to 2
    elif genre_type == 'kpop':
        markets = ['KR', 'US']
    else:
        markets = ['US']  # Single market for other genres
    
    print(f"🚀 Fast search: {len(search_terms)} terms in {len(markets)} markets")
    
    # 🚀 PARALLEL PROCESSING: Search multiple terms simultaneously
    def search_term_in_market(term, market):
        try:
            results = spotify.search(q=term, type='track', limit=10, market=market)
            songs = []
            for track in results['tracks']['items']:
                if track and track['popularity'] > 15:
                    song_info = f"'{track['name']}' by {track['artists'][0]['name']}"
                    songs.append(song_info)
            return songs
        except Exception as e:
            print(f"Error searching {term} in {market}: {e}")
            return []
    
    # Use ThreadPoolExecutor for parallel searches
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for term in search_terms[:6]:  # Limit to 6 terms for speed
            for market in markets:
                future = executor.submit(search_term_in_market, term, market)
                futures.append(future)
        
        # Collect results as they complete
        for future in as_completed(futures):
            try:
                songs = future.result(timeout=3)  # 3 second timeout per search
                found_songs.extend(songs)
                
                # 🚀 EARLY EXIT: Stop when we have enough songs
                if len(found_songs) >= 30:
                    break
            except Exception as e:
                print(f"Search future failed: {e}")
                continue
    
    # Remove duplicates and shuffle
    unique_songs = list(dict.fromkeys(found_songs))  # Preserve order while removing dupes
    random.shuffle(unique_songs)
    
    print(f"🎵 Fast result: {len(unique_songs)} unique songs for {genre_type}")
    return unique_songs[:20]  # Return top 20

def get_trending_songs_optimized():
    """🚀 OPTIMIZED: Faster trending songs with better caching"""
    if not SPOTIFY_ENABLED:
        return get_diverse_fallback_songs()
    
    current_time = time.time()
    
    # Check cache first
    if (current_time - trending_cache['last_updated']) < trending_cache['cache_duration']:
        print(f"⚡ Using cached trending songs ({len(trending_cache['songs'])} songs)")
        return trending_cache['songs']
    
    print(f"🔄 Refreshing trending cache...")
    
    try:
        trending_songs = []
        
        # 🚀 REDUCED: Use fewer search queries for faster loading
        priority_queries = [
            # Top mainstream hits
            "taylor swift", "drake", "billie eilish", "the weeknd", "dua lipa",
            "chart hits", "viral hits", "trending songs",
            
            # Regional priorities  
            "bollywood music", "kpop", "afrobeats", "latin music",
            
            # Major genres
            "indie rock", "hip hop", "electronic music", "pop music",
            
            # Decades
            "80s hits", "90s hits", "2000s hits",
        ]
        
        # 🚀 PARALLEL SEARCH: Search multiple queries simultaneously
        def search_query(query):
            try:
                results = spotify.search(q=query, type='track', limit=15, market='US')
                songs = []
                for track in results['tracks']['items']:
                    if track and track['popularity'] > 30:
                        song_info = f"'{track['name']}' by {track['artists'][0]['name']}"
                        songs.append(song_info)
                return songs
            except Exception as e:
                print(f"Error with query '{query}': {e}")
                return []
        
        # Use parallel processing for speed
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(search_query, query) for query in priority_queries]
            
            for future in as_completed(futures):
                try:
                    songs = future.result(timeout=5)  # 5 second timeout
                    for song in songs:
                        if song not in trending_songs:  # Avoid duplicates
                            trending_songs.append(song)
                    
                    # Stop early if we have enough
                    if len(trending_songs) >= 150:
                        break
                except Exception as e:
                    print(f"Future failed: {e}")
                    continue
        
        # Shuffle and cache
        random.shuffle(trending_songs)
        trending_cache['songs'] = trending_songs[:100]  # Keep top 100
        trending_cache['last_updated'] = current_time
        
        print(f"⚡ Cached {len(trending_cache['songs'])} trending songs")
        return trending_cache['songs']
        
    except Exception as e:
        print(f"Error updating trending songs: {e}")
        return get_diverse_fallback_songs()

# Keep existing helper functions
def extract_song_and_artist(query):
    """Extract song name and artist from query string"""
    patterns = [
        r"['\"]([^'\"]+)['\"] by (.+)",  # 'Song' by Artist
        r"([^'\"]+) by (.+)",           # Song by Artist
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            song_name = match.group(1).strip()
            artist_name = match.group(2).strip()
            artist_name = re.sub(r'[.!?–—,-]+.*$', '', artist_name).strip()
            return song_name, artist_name
    
    return None, None

def calculate_string_similarity(str1, str2):
    """Calculate similarity between two strings using word overlap"""
    if not str1 or not str2:
        return 0.0
    
    def normalize(text):
        return re.sub(r'[^\w\s]', '', text.lower()).strip()
    
    norm1 = normalize(str1)
    norm2 = normalize(str2)
    
    if norm1 == norm2:
        return 1.0
    
    if norm1 in norm2 or norm2 in norm1:
        return 0.9
    
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def calculate_match_score(target_song, target_artist, result_song, result_artist):
    """Calculate how well a search result matches the target song/artist"""
    song_score = calculate_string_similarity(target_song, result_song)
    artist_score = calculate_string_similarity(target_artist, result_artist)
    return (song_score * 0.6) + (artist_score * 0.4)

def get_diverse_fallback_songs():
    """Fast fallback songs for when Spotify is unavailable"""
    return [
        "'Anti-Hero' by Taylor Swift", "'God's Plan' by Drake", "'Bad Guy' by Billie Eilish",
        "'Blinding Lights' by The Weeknd", "'Levitating' by Dua Lipa", "'As It Was' by Harry Styles",
        "'Heat Waves' by Glass Animals", "'Good 4 U' by Olivia Rodrigo", "'Stay' by The Kid LAROI",
        "'Jai Ho' by A.R. Rahman", "'Tum Hi Ho' by Arijit Singh", "'Dynamite' by BTS",
        "'Despacito' by Luis Fonsi", "'Ye' by Burna Boy", "'Essence' by Wizkid",
        "'Motion Sickness' by Phoebe Bridgers", "'The Less I Know The Better' by Tame Impala",
        "'Bohemian Rhapsody' by Queen", "'Billie Jean' by Michael Jackson", "'Smells Like Teen Spirit' by Nirvana"
    ]
def get_smart_songs_from_results(tracks, limit=15):
    """🎯 Smart song selection - prioritize popular, recent, and high-quality songs"""
    if not tracks:
        return []
    
    smart_songs = []
    
    for track in tracks:
        if not track:
            continue
            
        # Calculate smart score based on multiple factors
        popularity = track.get('popularity', 0)
        
        # Bonus points for high popularity
        score = popularity
        
        # Bonus for recent releases (approximate - you could use release date)
        if popularity > 70:  # Very popular songs get extra points
            score += 20
        elif popularity > 50:  # Moderately popular
            score += 10
        
        # Bonus for having preview (indicates higher quality entry)
        if track.get('preview_url'):
            score += 5
        
        # Bonus for explicit content (often indicates higher engagement)
        if track.get('explicit'):
            score += 3
        
        # Only include songs with decent popularity (filter out obscure tracks)
        if popularity > 15:
            song_info = f"'{track['name']}' by {track['artists'][0]['name']}"
            smart_songs.append({
                'song': song_info,
                'score': score,
                'popularity': popularity
            })
    
    # Sort by smart score (highest first)
    smart_songs.sort(key=lambda x: x['score'], reverse=True)
    
    # Return just the song strings, prioritized by smart score
    result = [item['song'] for item in smart_songs[:limit]]
    
    print(f"🎯 Smart selection: Picked {len(result)} songs (popularity range: {smart_songs[0]['popularity'] if smart_songs else 0}-{smart_songs[-1]['popularity'] if smart_songs else 0})")
    
    return result

# Now update your existing search functions to use smart selection
def search_specific_genre_smart(genre_info):
    """🚀 ENHANCED: Use smart song selection for genre searches"""
    if not SPOTIFY_ENABLED:
        return []
    
    found_tracks = []  # Store actual track objects, not just strings
    genre_type = genre_info['type']
    
    # Use fewer search terms but get more results per term
    search_terms = genre_info['search_terms'][:6]  # Reduced from 8
    
    # Choose best markets for each genre
    if genre_type == 'bengali':
        markets = ['IN', 'US']
    elif genre_type in ['tamil', 'telugu', 'punjabi', 'hindi_bollywood']:
        markets = ['IN', 'US']
    elif genre_type == 'afrobeats':
        markets = ['NG', 'US']
    elif genre_type == 'kpop':
        markets = ['KR', 'US']
    else:
        markets = ['US']
    
    print(f"🎯 Smart genre search: {len(search_terms)} terms in {len(markets)} markets")
    
    try:
        for term in search_terms:
            for market in markets:
                try:
                    results = spotify.search(q=term, type='track', limit=15, market=market)
                    for track in results['tracks']['items']:
                        if track and track['popularity'] > 15:
                            found_tracks.append(track)
                    
                    # Stop if we have enough tracks
                    if len(found_tracks) >= 60:
                        break
                except Exception as e:
                    print(f"Error searching {term} in {market}: {e}")
                    continue
            
            if len(found_tracks) >= 60:
                break
    
    except Exception as e:
        print(f"Smart genre search error: {e}")
        return []
    
    # Use smart selection to pick the best songs
    return get_smart_songs_from_results(found_tracks, 20)

def search_artist_songs_smart(artist_name, limit=15):
    """🎤 Enhanced artist search with smart selection"""
    if not SPOTIFY_ENABLED:
        return []
    
    found_tracks = []
    print(f"🎯 Smart artist search: {artist_name}")
    
    try:
        # Step 1: Find the most popular artist
        artist_search_results = spotify.search(
            q=f'artist:"{artist_name}"', 
            type='artist', 
            limit=10, 
            market='US'
        )
        
        best_artist = None
        highest_popularity = 0
        
        for artist in artist_search_results['artists']['items']:
            artist_popularity = artist.get('popularity', 0)
            name_match = (
                artist_name.lower() in artist['name'].lower() or
                artist['name'].lower() in artist_name.lower()
            )
            
            if name_match and artist_popularity > highest_popularity:
                highest_popularity = artist_popularity
                best_artist = artist
        
        if not best_artist:
            return []
        
        selected_artist = best_artist['name']
        artist_id = best_artist['id']
        
        # Step 2: Get their top tracks (these are pre-sorted by popularity)
        top_tracks = spotify.artist_top_tracks(artist_id, country='US')
        for track in top_tracks['tracks']:
            if track and track['popularity'] > 10:
                found_tracks.append(track)
        
        # Step 3: Get additional songs if needed
        if len(found_tracks) < 12:
            additional_results = spotify.search(
                q=f'artist:"{selected_artist}"', 
                type='track', 
                limit=25, 
                market='US'
            )
            
            for track in additional_results['tracks']['items']:
                if (track and 
                    track['popularity'] > 15 and 
                    track['artists'][0]['name'] == selected_artist):
                    found_tracks.append(track)
                
                if len(found_tracks) >= 20:
                    break
        
        # Use smart selection (but for artists, we already have good tracks)
        return get_smart_songs_from_results(found_tracks, limit)
        
    except Exception as e:
        print(f"❌ Smart artist search failed: {e}")
        return []

search_specific_genre = search_specific_genre_smart
search_artist_songs = search_artist_songs_smart
get_trending_songs = get_trending_songs_optimized  # 👈 ADD THIS LINE

__all__ = [
    'spotify',  # Export the client
    'get_trending_songs', 
    'search_spotify_song',
    'search_specific_genre', 
    'search_artist_songs',
    'SPOTIFY_ENABLED'
]