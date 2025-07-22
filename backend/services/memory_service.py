# ------------------------------------------------------------
# © 2025 Samia Islam. All rights reserved.
# This file is part of the "YAIN" project.
# Released under CC BY-NC 4.0 license.
# For demo and educational use only — not for commercial use.
# ------------------------------------------------------------
# Memory service for YAIN
# Handles memory management for music suggestions and user preferences


import re

def normalize_song_title(song):
    """Normalize song title for better comparison"""
    # Remove quotes and extra punctuation
    normalized = re.sub(r"['\"]", "", song.lower())
    # Remove extra spaces
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def extract_song_parts(song):
    """Extract song name and artist from formatted string"""
    # Handle formats like "'Song' by Artist" or "Song by Artist"
    patterns = [
        r"['\"]([^'\"]+)['\"] by (.+)",  # 'Song' by Artist
        r"([^'\"]+) by (.+)",           # Song by Artist
    ]
    
    for pattern in patterns:
        match = re.search(pattern, song, re.IGNORECASE)
        if match:
            song_name = match.group(1).strip()
            artist_name = match.group(2).strip()
            return song_name.lower(), artist_name.lower()
    
    # If no pattern matches, return the whole string
    return song.lower(), ""

def filter_trending_songs(trending_songs, suggested_songs):
    """🧠 IMPROVED MEMORY: Remove already suggested songs with better matching"""
    
    # Debug logging
    print(f"\n🧠 === MEMORY FILTER DEBUG ===")
    print(f"📥 Input: {len(trending_songs)} trending songs")
    print(f"🧠 Memory: {len(suggested_songs)} suggested songs")
    
    if not suggested_songs:
        print(f"✅ No memory to filter against - returning all {len(trending_songs)} songs")
        return trending_songs
    
    print(f"🔍 Songs to filter out:")
    for i, song in enumerate(suggested_songs):
        print(f"  {i+1}. {song}")
    
    filtered = []
    blocked_count = 0
    
    # Create normalized versions of suggested songs
    suggested_normalized = []
    for song in suggested_songs:
        song_name, artist_name = extract_song_parts(song)
        suggested_normalized.append({
            'original': song,
            'song_name': song_name,
            'artist_name': artist_name,
            'full_normalized': normalize_song_title(song)
        })
    
    for trending_song in trending_songs:
        trending_name, trending_artist = extract_song_parts(trending_song)
        trending_normalized = normalize_song_title(trending_song)
        
        is_duplicate = False
        
        # Check multiple matching strategies
        for suggested in suggested_normalized:
            # Strategy 1: Exact normalized match
            if trending_normalized == suggested['full_normalized']:
                is_duplicate = True
                blocked_count += 1
                print(f"🚫 BLOCKED (exact): {trending_song} matches {suggested['original']}")
                break
            
            # Strategy 2: Song name match (more flexible)
            if trending_name and suggested['song_name']:
                if trending_name in suggested['song_name'] or suggested['song_name'] in trending_name:
                    is_duplicate = True
                    blocked_count += 1
                    print(f"🚫 BLOCKED (song name): {trending_song} matches {suggested['original']}")
                    break
            
            # Strategy 3: Artist name match (prevent same artist flooding)
            if trending_artist and suggested['artist_name']:
                if trending_artist == suggested['artist_name']:
                    # Same artist - check if song names are similar
                    if trending_name and suggested['song_name']:
                        # Allow same artist if song names are very different
                        name_similarity = len(set(trending_name.split()) & set(suggested['song_name'].split()))
                        if name_similarity >= 1:  # At least one word in common
                            is_duplicate = True
                            blocked_count += 1
                            print(f"🚫 BLOCKED (same artist, similar song): {trending_song} matches {suggested['original']}")
                            break
        
        if not is_duplicate:
            filtered.append(trending_song)
        
    print(f"📊 MEMORY FILTER RESULTS:")
    print(f"  🚫 Blocked: {blocked_count} songs")
    print(f"  ✅ Remaining: {len(filtered)} songs")
    print(f"  🎯 Filter effectiveness: {(blocked_count / len(trending_songs) * 100):.1f}%")
    
    if len(filtered) == 0:
        print(f"⚠️ WARNING: All songs filtered out! Memory might be too aggressive.")
        # Return some songs to prevent complete failure
        return trending_songs[-5:]  # Return last 5 songs as emergency fallback
    
    print(f"🧠 === MEMORY FILTER COMPLETE ===\n")
    return filtered

def create_memory_stats(suggested_songs, available_songs, request_type):
    """Create enhanced memory statistics for response"""
    
    # Calculate filter effectiveness
    original_count = len(available_songs) if hasattr(available_songs, '__len__') else 0
    memory_count = len(suggested_songs) if suggested_songs else 0
    
    # Determine if memory is working
    memory_working = memory_count > 0
    
    print(f"📊 MEMORY STATS CALCULATION:")
    print(f"  🧠 Songs remembered: {memory_count}")
    print(f"  📦 Available songs: {original_count}")
    print(f"  🎯 Request type: {request_type}")
    print(f"  ✅ Memory active: {memory_working}")
    
    return {
        "songs_remembered": memory_count,
        "songs_available": original_count,
        "request_type": request_type,
        "memory_efficiency": memory_count / max(1, memory_count + original_count),
        "filtering_active": memory_working,
        "memory_working": memory_working,  # This is what frontend checks!
        "status": "active" if memory_working else "inactive"
    }

def validate_memory_system(suggested_songs, new_song=None):
    """🔧 NEW: Validate that memory system is working correctly"""
    print(f"\n🔍 === MEMORY SYSTEM VALIDATION ===")
    
    if not suggested_songs:
        print(f"📝 Memory is empty - first suggestion")
        return {
            "valid": True,
            "status": "empty",
            "message": "Memory system ready - no previous suggestions"
        }
    
    print(f"🧠 Memory contains {len(suggested_songs)} songs:")
    for i, song in enumerate(suggested_songs):
        print(f"  {i+1}. {song}")
    
    if new_song:
        # Check if new song would be a duplicate
        for existing_song in suggested_songs:
            existing_name, existing_artist = extract_song_parts(existing_song)
            new_name, new_artist = extract_song_parts(new_song)
            
            if existing_name and new_name:
                if existing_name in new_name or new_name in existing_name:
                    print(f"🚨 DUPLICATE DETECTED!")
                    print(f"  Existing: {existing_song}")
                    print(f"  New: {new_song}")
                    return {
                        "valid": False,
                        "status": "duplicate",
                        "message": f"Song '{new_song}' is too similar to '{existing_song}'"
                    }
    
    print(f"✅ Memory system working correctly")
    return {
        "valid": True,
        "status": "active",
        "message": f"Memory tracking {len(suggested_songs)} unique songs"
    }

def get_memory_insights(suggested_songs, request_type):
    """🧠 ADVANCED: Get insights about user's music preferences from memory"""
    if not suggested_songs:
        return {
            'total_songs': 0,
            'unique_artists': 0,
            'genre_patterns': [],
            'listening_diversity': 0
        }
    
    # Analyze remembered songs for patterns
    artists_count = {}
    genres_detected = []
    
    for song in suggested_songs:
        _, artist = extract_song_parts(song)
        if artist:
            artists_count[artist] = artists_count.get(artist, 0) + 1
    
    # Detect genre patterns based on request types
    # This could be expanded with more sophisticated analysis
    
    return {
        'total_songs': len(suggested_songs),
        'unique_artists': len(artists_count),
        'top_artists': sorted(artists_count.items(), key=lambda x: x[1], reverse=True)[:3],
        'listening_diversity': len(artists_count) / max(1, len(suggested_songs)),
        'current_request_type': request_type
    }

def smart_song_selection(available_songs, suggested_songs, user_preferences=None):
    """🎯 SMART SELECTION: Choose best song based on memory and preferences"""
    if not available_songs:
        return None
    
    # Filter out already suggested songs
    filtered_songs = filter_trending_songs(available_songs, suggested_songs)
    
    if not filtered_songs:
        print("⚠️ No new songs available after filtering")
        return None
    
    # If no user preferences, return first available
    if not user_preferences:
        return filtered_songs[0]
    
    # TODO: Implement smart selection based on user preferences
    # For now, return first available filtered song
    return filtered_songs[0]

def update_memory_context(suggested_songs, new_song, context_data=None):
    """📊 CONTEXT: Update memory with contextual information"""
    if not new_song:
        return suggested_songs
    
    # Add new song to memory if not already present
    if new_song not in suggested_songs:
        updated_memory = suggested_songs + [new_song]
        print(f"🧠 Memory updated: {len(suggested_songs)} → {len(updated_memory)} songs")
        return updated_memory
    
    return suggested_songs

def analyze_memory_patterns(suggested_songs):
    """📈 ANALYTICS: Analyze patterns in user's music memory"""
    if len(suggested_songs) < 2:
        return {"insufficient_data": True}
    
    # Extract artists and songs
    artists = []
    song_names = []
    
    for song in suggested_songs:
        song_name, artist = extract_song_parts(song)
        if song_name:
            song_names.append(song_name)
        if artist:
            artists.append(artist)
    
    # Calculate diversity metrics
    unique_artists = len(set(artists))
    total_songs = len(suggested_songs)
    artist_diversity = unique_artists / max(1, total_songs)
    
    # Find most requested artist
    from collections import Counter
    artist_counts = Counter(artists)
    most_popular_artist = artist_counts.most_common(1)[0] if artist_counts else None
    
    return {
        "total_songs_remembered": total_songs,
        "unique_artists": unique_artists,
        "artist_diversity_score": round(artist_diversity, 2),
        "most_popular_artist": most_popular_artist[0] if most_popular_artist else None,
        "most_popular_artist_count": most_popular_artist[1] if most_popular_artist else 0,
        "memory_patterns_detected": True
    }

def cleanup_old_memory(suggested_songs, max_memory_size=50):
    """🧹 CLEANUP: Keep memory size manageable"""
    if len(suggested_songs) <= max_memory_size:
        return suggested_songs
    
    # Keep the most recent songs
    cleaned_memory = suggested_songs[-max_memory_size:]
    print(f"🧹 Memory cleaned: {len(suggested_songs)} → {len(cleaned_memory)} songs")
    return cleaned_memory

def get_memory_summary(suggested_songs):
    """📋 SUMMARY: Get a summary of current memory state"""
    if not suggested_songs:
        return "Memory is empty - no songs suggested yet."
    
    patterns = analyze_memory_patterns(suggested_songs)
    
    if patterns.get("insufficient_data"):
        return f"Memory contains {len(suggested_songs)} song(s). Need more data for pattern analysis."
    
    summary = f"""Memory Summary:
• {patterns['total_songs_remembered']} songs remembered
• {patterns['unique_artists']} unique artists
• Diversity score: {patterns['artist_diversity_score']}/1.0
• Most requested: {patterns.get('most_popular_artist', 'None')} ({patterns.get('most_popular_artist_count', 0)}x)"""
    
    return summary