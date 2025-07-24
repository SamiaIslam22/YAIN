# ------------------------------------------------------------
# © 2025 Samia Islam. All rights reserved.
# This file is part of the "YAIN" project.
# Released under CC BY-NC 4.0 license.
# For demo and educational use only — not for commercial use.
# ------------------------------------------------------------

# Spotify Web API integration module
# Handles track searches, genre filtering, and trending song retrieval with caching optimization

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import time
import random
import re
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed

# Cache configuration for performance optimization
trending_cache = {
    'songs': [],
    'last_updated': 0,
    'cache_duration': 3600  # 1 hour cache expiration
}

# Search result cache to prevent duplicate API calls
search_cache = {}
cache_ttl = 1800  # 30 minute cache TTL

def init_spotify():
    """
    Initialize Spotify Web API client with application credentials
    
    Returns:
        tuple: (spotify_client, enabled_status) - Client instance and boolean status
    """
    try:
        spotify_credentials = SpotifyClientCredentials(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
        )
        spotify = spotipy.Spotify(client_credentials_manager=spotify_credentials)
        return spotify, True
    except:
        print("Spotify credentials not found")
        return None, False

# Initialize client on module import
spotify, SPOTIFY_ENABLED = init_spotify()

def search_spotify_song(query):
    """
    Search Spotify for a specific song with caching and optimized API usage
    
    Args:
        query (str): Song search query in format "'Song' by Artist"
        
    Returns:
        dict: Track metadata including name, artist, URLs, and match score
        None: If no suitable match found or API unavailable
    """
    if not SPOTIFY_ENABLED:
        return None
    
    print(f"\n=== SPOTIFY SEARCH ===")
    print(f"Query: {query}")
    
    # Check cache before making API call
    cache_key = query.lower().strip()
    current_time = time.time()
    
    if cache_key in search_cache:
        cached_result, cached_time = search_cache[cache_key]
        if current_time - cached_time < cache_ttl:
            print(f"Cache hit! Returning cached result for: {query}")
            return cached_result
    
    try:
        # Parse query string to extract song and artist components
        song_name, artist_name = extract_song_and_artist(query)
        
        if not song_name or not artist_name:
            print(f"Could not parse song and artist from query")
            return None
        
        print(f"Searching for: '{song_name}' by '{artist_name}'")
        
        # Define search strategies ordered by accuracy
        search_strategies = [
            f'track:"{song_name}" artist:"{artist_name}"',  # Exact field matching
            f'"{song_name}" "{artist_name}"'                # General search fallback
        ]
        
        best_match = None
        best_score = 0.0
        
        for i, strategy in enumerate(search_strategies, 1):
            print(f"Strategy {i}/2: {strategy}")
            
            try:
                # Execute search with single market for consistency
                results = spotify.search(q=strategy, type='track', limit=5, market='US')
                tracks = results['tracks']['items']
                
                if not tracks:
                    print(f"  No results")
                    continue
                
                print(f"  Found {len(tracks)} results")
                
                # Score top results to find best match
                for j, track in enumerate(tracks[:3]):
                    if not track:
                        continue
                        
                    score = calculate_match_score(
                        song_name, artist_name,
                        track['name'], track['artists'][0]['name']
                    )
                    
                    print(f"  {track['name']} by {track['artists'][0]['name']} (score: {score:.2f})")
                    
                    if score > best_score:
                        best_score = score
                        best_match = track
                        print(f"  NEW BEST! Score: {score:.2f}")
                
                # Early termination for high-confidence matches
                if best_score >= 0.8:
                    print(f"High-confidence match found (score: {best_score:.2f}), stopping search")
                    break
                    
            except Exception as e:
                print(f"  Error: {e}")
                continue
        
        # Process and format result
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
            
            print(f"Found: '{result['name']}' by {result['artist']} (score: {best_score:.2f})")
        else:
            print(f"No suitable match found (best score: {best_score:.2f})")
        
        # Cache result for future requests
        search_cache[cache_key] = (result, current_time)
        
        return result
                
    except Exception as e:
        print(f"Spotify search error: {e}")
        return None

def search_specific_genre_optimized(genre_info):
    """
    Search for songs within specific genre using parallel processing
    
    Args:
        genre_info (dict): Genre metadata containing type and search terms
        
    Returns:
        list: List of formatted song strings matching the genre
    """
    if not SPOTIFY_ENABLED:
        return []
    
    found_songs = []
    genre_type = genre_info['type']
    
    # Limit search terms for performance optimization
    search_terms = genre_info['search_terms'][:8]
    
    # Select optimal markets based on genre type
    if genre_type == 'bengali':
        markets = ['IN', 'US']
    elif genre_type in ['tamil', 'telugu', 'punjabi', 'hindi_bollywood']:
        markets = ['IN', 'US']
    elif genre_type == 'afrobeats':
        markets = ['NG', 'US']
    elif genre_type == 'kpop':
        markets = ['KR', 'US']
    else:
        markets = ['US']  # Default to US market
    
    print(f"Genre search: {len(search_terms)} terms in {len(markets)} markets")
    
    # Parallel search function for threading
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
    
    # Execute parallel searches with thread pool
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for term in search_terms[:6]:  # Limit concurrent searches
            for market in markets:
                future = executor.submit(search_term_in_market, term, market)
                futures.append(future)
        
        # Collect results as they complete with timeout
        for future in as_completed(futures):
            try:
                songs = future.result(timeout=3)  # 3 second timeout per search
                found_songs.extend(songs)
                
                # Early termination when sufficient results found
                if len(found_songs) >= 30:
                    break
            except Exception as e:
                print(f"Search future failed: {e}")
                continue
    
    # Remove duplicates while preserving order and shuffle results
    unique_songs = list(dict.fromkeys(found_songs))
    random.shuffle(unique_songs)
    
    print(f"Genre search result: {len(unique_songs)} unique songs for {genre_type}")
    return unique_songs[:20]  # Return top 20 results

def get_trending_songs_optimized():
    """
    Retrieve trending songs using cached results and parallel processing
    
    Returns:
        list: List of formatted trending song strings
    """
    if not SPOTIFY_ENABLED:
        return get_diverse_fallback_songs()
    
    current_time = time.time()
    
    # Return cached results if still valid
    if (current_time - trending_cache['last_updated']) < trending_cache['cache_duration']:
        print(f"Using cached trending songs ({len(trending_cache['songs'])} songs)")
        return trending_cache['songs']
    
    print(f"Refreshing trending cache...")
    
    try:
        trending_songs = []
        
        # Define priority search queries for trending content
        priority_queries = [
            # Mainstream artists
            "taylor swift", "drake", "billie eilish", "the weeknd", "dua lipa",
            "chart hits", "viral hits", "trending songs",
            
            # Regional music priorities  
            "bollywood music", "kpop", "afrobeats", "latin music",
            
            # Genre categories
            "indie rock", "hip hop", "electronic music", "pop music",
            
            # Era-based searches
            "80s hits", "90s hits", "2000s hits",
        ]
        
        # Parallel search function for trending queries
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
        
        # Execute parallel searches with timeout handling
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(search_query, query) for query in priority_queries]
            
            for future in as_completed(futures):
                try:
                    songs = future.result(timeout=5)  # 5 second timeout
                    for song in songs:
                        if song not in trending_songs:  # Prevent duplicates
                            trending_songs.append(song)
                    
                    # Early termination when sufficient results collected
                    if len(trending_songs) >= 150:
                        break
                except Exception as e:
                    print(f"Future failed: {e}")
                    continue
        
        # Randomize results and update cache
        random.shuffle(trending_songs)
        trending_cache['songs'] = trending_songs[:100]  # Store top 100 results
        trending_cache['last_updated'] = current_time
        
        print(f"Cached {len(trending_cache['songs'])} trending songs")
        return trending_cache['songs']
        
    except Exception as e:
        print(f"Error updating trending songs: {e}")
        return get_diverse_fallback_songs()

def extract_song_and_artist(query):
    """
    Parse query string to extract song name and artist using regex patterns
    
    Args:
        query (str): Query string in various formats
        
    Returns:
        tuple: (song_name, artist_name) or (None, None) if parsing fails
    """
    patterns = [
        r"['\"]([^'\"]+)['\"] by (.+)",  # 'Song' by Artist format
        r"([^'\"]+) by (.+)",           # Song by Artist format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            song_name = match.group(1).strip()
            artist_name = match.group(2).strip()
            # Clean artist name by removing trailing punctuation
            artist_name = re.sub(r'[.!?–—,-]+.*$', '', artist_name).strip()
            return song_name, artist_name
    
    return None, None

def calculate_string_similarity(str1, str2):
    """
    Calculate similarity score between two strings using word overlap analysis
    
    Args:
        str1, str2 (str): Strings to compare
        
    Returns:
        float: Similarity score between 0.0 and 1.0
    """
    if not str1 or not str2:
        return 0.0
    
    def normalize(text):
        return re.sub(r'[^\w\s]', '', text.lower()).strip()
    
    norm1 = normalize(str1)
    norm2 = normalize(str2)
    
    # Check for exact match
    if norm1 == norm2:
        return 1.0
    
    # Check for substring containment
    if norm1 in norm2 or norm2 in norm1:
        return 0.9
    
    # Calculate word overlap using Jaccard similarity
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def calculate_match_score(target_song, target_artist, result_song, result_artist):
    """
    Calculate weighted match score between target and result track metadata
    
    Args:
        target_song, target_artist (str): Expected track information
        result_song, result_artist (str): API result track information
        
    Returns:
        float: Weighted match score (song 60%, artist 40%)
    """
    song_score = calculate_string_similarity(target_song, result_song)
    artist_score = calculate_string_similarity(target_artist, result_artist)
    return (song_score * 0.6) + (artist_score * 0.4)

def get_diverse_fallback_songs():
    """
    Provide hardcoded song list as fallback when Spotify API is unavailable
    
    Returns:
        list: Curated list of popular songs across various genres and eras
    """
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
    """
    Apply intelligent selection algorithm to prioritize high-quality tracks
    
    Args:
        tracks (list): List of Spotify track objects
        limit (int): Maximum number of songs to return
        
    Returns:
        list: Prioritized list of formatted song strings
    """
    if not tracks:
        return []
    
    smart_songs = []
    
    for track in tracks:
        if not track:
            continue
            
        # Calculate composite score based on multiple quality factors
        popularity = track.get('popularity', 0)
        score = popularity
        
        # Apply popularity bonuses
        if popularity > 70:  # High popularity boost
            score += 20
        elif popularity > 50:  # Medium popularity boost
            score += 10
        
        # Bonus for preview availability (indicates complete metadata)
        if track.get('preview_url'):
            score += 5
        
        # Bonus for explicit content (often indicates higher engagement)
        if track.get('explicit'):
            score += 3
        
        # Filter out low-popularity tracks
        if popularity > 15:
            song_info = f"'{track['name']}' by {track['artists'][0]['name']}"
            smart_songs.append({
                'song': song_info,
                'score': score,
                'popularity': popularity
            })
    
    # Sort by composite score in descending order
    smart_songs.sort(key=lambda x: x['score'], reverse=True)
    
    # Extract song strings from sorted results
    result = [item['song'] for item in smart_songs[:limit]]
    
    print(f"Smart selection: Picked {len(result)} songs (popularity range: {smart_songs[0]['popularity'] if smart_songs else 0}-{smart_songs[-1]['popularity'] if smart_songs else 0})")
    
    return result

def search_specific_genre_smart(genre_info):
    """
    Enhanced genre search using intelligent track selection algorithm
    
    Args:
        genre_info (dict): Genre metadata with type and search terms
        
    Returns:
        list: Intelligently selected songs matching the genre
    """
    if not SPOTIFY_ENABLED:
        return []
    
    found_tracks = []  # Store track objects for intelligent processing
    genre_type = genre_info['type']
    
    # Optimize search terms for better API efficiency
    search_terms = genre_info['search_terms'][:6]
    
    # Select markets based on genre geographic relevance
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
    
    print(f"Smart genre search: {len(search_terms)} terms in {len(markets)} markets")
    
    try:
        for term in search_terms:
            for market in markets:
                try:
                    results = spotify.search(q=term, type='track', limit=15, market=market)
                    for track in results['tracks']['items']:
                        if track and track['popularity'] > 15:
                            found_tracks.append(track)
                    
                    # Early termination for performance
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
    
    # Apply intelligent selection to track objects
    return get_smart_songs_from_results(found_tracks, 20)

def search_artist_songs_smart(artist_name, limit=15):
    """
    Enhanced artist search combining top tracks and catalog search
    
    Args:
        artist_name (str): Name of artist to search for
        limit (int): Maximum number of songs to return
        
    Returns:
        list: Intelligently selected songs by the artist
    """
    if not SPOTIFY_ENABLED:
        return []
    
    found_tracks = []
    print(f"Smart artist search: {artist_name}")
    
    try:
        # Step 1: Find the most relevant artist by popularity
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
        
        # Step 2: Get top tracks (pre-sorted by popularity)
        top_tracks = spotify.artist_top_tracks(artist_id, country='US')
        for track in top_tracks['tracks']:
            if track and track['popularity'] > 10:
                found_tracks.append(track)
        
        # Step 3: Supplement with additional catalog search if needed
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
        
        # Apply intelligent selection to collected tracks
        return get_smart_songs_from_results(found_tracks, limit)
        
    except Exception as e:
        print(f"Smart artist search failed: {e}")
        return []

# Function aliases for backward compatibility
search_specific_genre = search_specific_genre_smart
search_artist_songs = search_artist_songs_smart
get_trending_songs = get_trending_songs_optimized

# Module exports
__all__ = [
    'spotify',  # Spotify client instance
    'get_trending_songs', 
    'search_spotify_song',
    'search_specific_genre', 
    'search_artist_songs',
    'SPOTIFY_ENABLED'
]