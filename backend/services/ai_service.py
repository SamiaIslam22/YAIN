# ------------------------------------------------------------
# © 2025 Samia Islam. All rights reserved.
# This file is part of the "YAIN" project.
# Released under CC BY-NC 4.0 license.
# For demo and educational use only — not for commercial use.
# ------------------------------------------------------------

import google.generativeai as genai
import os
import re

# Configure Gemini AI
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

# In ai_service.py - Enhanced ARTIST SEARCH DETECTION

# Replace the ARTIST SEARCH DETECTION section in ai_service.py

# 🎤 ENHANCED ARTIST SEARCH DETECTION
def detect_artist_search(message_lower):
    """Detect artist search requests"""
    
    # Pattern 1: "give me songs by [artist]"
    pattern1 = r'(?:give me|show me|find|get|want|play)\s+(?:some\s+)?(?:songs?|music|tracks?)\s+(?:by|from)\s+(.+?)(?:\s|$|[.!?])'
    match1 = re.search(pattern1, message_lower, re.IGNORECASE)
    if match1:
        artist = match1.group(1).strip()
        return clean_and_validate_artist(artist)
    
    # Pattern 2: "songs by [artist]"
    pattern2 = r'(?:^|\s)(?:songs?|music|tracks?)\s+(?:by|from)\s+(.+?)(?:\s|$|[.!?])'
    match2 = re.search(pattern2, message_lower, re.IGNORECASE)
    if match2:
        artist = match2.group(1).strip()
        return clean_and_validate_artist(artist)
    
    # Pattern 3: "[artist] songs/music"
    pattern3 = r'(?:^|\s)(.+?)\s+(?:songs?|music|tracks?)(?:\s|$|[.!?])'
    match3 = re.search(pattern3, message_lower, re.IGNORECASE)
    if match3:
        artist = match3.group(1).strip()
        validated = clean_and_validate_artist(artist)
        if validated and len(validated.split()) <= 2:
            return validated
    
    # 🆕 Pattern 4: Single artist names (like "drake", "taylor", "keshi")
    stripped_message = message_lower.strip()
    words = stripped_message.split()
    
    # If it's 1-3 words, might be an artist name
    if 1 <= len(words) <= 3 and len(stripped_message) >= 2:
        # Only exclude obvious mood/command words
        non_artist_words = {
            'happy', 'sad', 'chill', 'angry', 'excited', 'love', 'hate',
            'music', 'song', 'songs', 'play', 'listen', 'find', 'search',
            'hello', 'hi', 'hey', 'thanks', 'help', 'please', 'yes', 'no'
        }
        
        # If it's not obviously a mood/command, treat as artist name
        if not any(word in non_artist_words for word in words):
            potential_artist = ' '.join(words).title()
            print(f"🎤 Single artist detected: {potential_artist}")
            return potential_artist
    
    return None

def check_if_artist_exists(query, spotify_client):
    """🔍 DYNAMIC: Check if query is an artist name using Spotify search"""
    if not spotify_client:
        return None
    
    print(f"🔍 Checking if '{query}' is an artist...")
    
    try:
        # Search for artists with this name
        results = spotify_client.search(q=f'artist:"{query}"', type='artist', limit=10, market='US')
        artists = results['artists']['items']
        
        if not artists:
            print(f"❌ No artists found for '{query}'")
            return None
        
        # Find the most popular/relevant artist
        best_artist = None
        highest_popularity = 0
        
        for artist in artists:
            artist_name = artist['name'].lower()
            query_lower = query.lower()
            popularity = artist.get('popularity', 0)
            
            print(f"  👤 Found: {artist['name']} (popularity: {popularity})")
            
            # Check name match quality
            exact_match = artist_name == query_lower
            contains_match = query_lower in artist_name or artist_name in query_lower
            
            # Prioritize exact matches, then popular artists
            score = 0
            if exact_match:
                score = popularity + 100  # Boost exact matches
            elif contains_match:
                score = popularity + 50   # Boost partial matches
            else:
                score = popularity
            
            if score > highest_popularity:
                highest_popularity = score
                best_artist = artist
                print(f"    ⭐ New best: {artist['name']} (score: {score})")
        
        # Only return if we found a reasonably popular artist
        if best_artist and best_artist.get('popularity', 0) > 15:
            print(f"✅ Artist detected: {best_artist['name']} (popularity: {best_artist['popularity']})")
            return {
                'name': best_artist['name'],
                'id': best_artist['id'],
                'popularity': best_artist['popularity'],
                'genres': best_artist.get('genres', [])
            }
        else:
            print(f"❌ No popular artists found for '{query}'")
            return None
            
    except Exception as e:
        print(f"❌ Error checking artist: {e}")
        return None

def is_potential_artist_query(message):
    """🎯 Determine if a message might be an artist name"""
    message = message.strip().lower()
    words = message.split()
    
    # Skip obvious non-artist patterns
    non_artist_indicators = {
        # Emotions/moods
        'happy', 'sad', 'angry', 'excited', 'chill', 'relaxed', 'stressed',
        'love', 'hate', 'tired', 'energetic', 'lonely', 'confident',
        
        # Commands/requests
        'play', 'find', 'search', 'give', 'show', 'get', 'want', 'need',
        'hello', 'hi', 'hey', 'thanks', 'help', 'please',
        
        # Music terms (without artist context)
        'music', 'song', 'songs', 'playlist', 'album', 'track', 'tracks',
        
        # Descriptors
        'good', 'bad', 'best', 'worst', 'new', 'old', 'latest', 'trending',
        'popular', 'random', 'any', 'some', 'something', 'anything',
        
        # Genres (will be caught by genre detection)
        'rock', 'pop', 'rap', 'jazz', 'blues', 'country', 'electronic',
        'classical', 'folk', 'metal', 'punk', 'reggae', 'disco',
        
        # Languages/regions (will be caught by region detection)
        'hindi', 'spanish', 'korean', 'japanese', 'french', 'german',
        'bollywood', 'kpop', 'latin', 'african', 'american', 'british'
    }
    
    # Check basic criteria for potential artist name
    if len(words) > 4:  # Too many words, probably not an artist
        return False
    
    if len(message) < 2:  # Too short
        return False
    
    # If all words are in non-artist list, probably not an artist
    if all(word in non_artist_indicators for word in words):
        return False
    
    # If it contains obvious command patterns, not an artist
    command_patterns = [
        r'give me.*',
        r'play some.*',
        r'find.*music',
        r'i want.*',
        r'show me.*',
        r'.*songs? (by|from).*',
    ]
    
    for pattern in command_patterns:
        if re.search(pattern, message):
            return False
    
    # If we get here, it might be an artist name
    print(f"🤔 '{message}' might be an artist name - checking Spotify...")
    return True

def clean_and_validate_artist(artist_name):
    """Simple artist name cleanup"""
    if not artist_name or len(artist_name.strip()) < 2:
        return None
    
    # Basic cleanup
    artist_name = artist_name.strip()
    artist_name = re.sub(r'^(?:the|some)\s+', '', artist_name, flags=re.IGNORECASE)
    artist_name = re.sub(r'\s+(?:please|pls)$', '', artist_name, flags=re.IGNORECASE)
    
    return artist_name.title()

def analyze_user_request(user_message):
    """🎭 ENHANCED REGIONAL MUSIC DETECTION - Bengali, Tamil, Afrobeats, etc."""
    message_lower = user_message.lower()
    try:
        from .spotify_service import spotify
    except ImportError:
        from spotify_service import spotify
    # 🎵 SPECIFIC SONG SEARCH DETECTION (keep existing)
    specific_song_patterns = [
        r'^(.+?)\s+by\s+(.+?)$',
        r'(?:play|find|search|give me|want|show me)\s+(.+?)\s+by\s+(.+?)(?:\s|$)',
    ]
    
    for pattern in specific_song_patterns:
        match = re.search(pattern, message_lower, re.IGNORECASE)
        if match:
            song_name = match.group(1).strip()
            artist_name = match.group(2).strip()
            
            if len(song_name) > 1 and len(artist_name) > 1:
                search_query = f"'{song_name.title()}' by {artist_name.title()}"
                return {
                    'type': 'specific_song',
                    'song_name': song_name.title(),
                    'artist_name': artist_name.title(),
                    'search_query': search_query,
                    'search_terms': [search_query],
                    'genre_hint': f"the song '{song_name.title()}' by {artist_name.title()}"
                }
    
    # 🎤 ENHANCED ARTIST SEARCH DETECTION (keep your existing patterns)
    artist_patterns = [
        # "give me songs by keshi" 
        r'(?:give me|play|find|show me|want)\s+(?:songs?|music|tracks?)\s+(?:by|from)\s+(.+?)(?:\s|$)',
        # "songs by keshi"
        r'(?:^|\s)songs?\s+(?:by|from)\s+(.+?)(?:\s|$)',
        # "keshi songs" 
        r'(?:^|\s)(.+?)\s+songs?(?:\s|$)',
        # "music from keshi"
        r'(?:music|tracks?)\s+(?:by|from)\s+(.+?)(?:\s|$)',
        # Direct artist mention patterns
        r'(?:^|\s)(.+?)\s+(?:music|artist|band)(?:\s|$)',
    ]
    
    for pattern in artist_patterns:
        match = re.search(pattern, message_lower, re.IGNORECASE)
        if match:
            artist_name = match.group(1).strip()
            
            # Enhanced exclusion - remove common non-artist words
            excluded_words = [
                'happy', 'sad', 'chill', 'me', 'some', 'good', 'new', 'old', 'best',
                'favorite', 'latest', 'popular', 'trending', 'hot', 'cool', 'nice',
                'great', 'awesome', 'amazing', 'perfect', 'love', 'like', 'want',
                'need', 'get', 'find', 'search', 'play', 'listen', 'hear', 'show',
                'give', 'the', 'a', 'an', 'and', 'or', 'but', 'for', 'with',
                'random', 'any', 'something', 'anything'
            ]
            
            # Check if artist name is valid
            if (len(artist_name) > 2 and 
                artist_name not in excluded_words and
                not any(word in artist_name for word in ['songs', 'music', 'tracks']) and
                len(artist_name.split()) <= 3):  # Artists usually don't have super long names
                
                # Check if this artist exists on Spotify
                artist_info = check_if_artist_exists(artist_name, spotify)
                if artist_info:
                    print(f"🎤 Explicit artist detected: {artist_info['name']}")
                    return {
                        'type': 'artist_search',
                        'artist_name': artist_info['name'],
                        'artist_id': artist_info['id'],
                        'search_terms': [f"{artist_info['name']} songs", f"{artist_info['name']} popular", f"{artist_info['name']} hits"],
                        'genre_hint': f'songs by {artist_info["name"]}'
                    }
    
    # 🚀 DYNAMIC ARTIST DETECTION - Check if single word/phrase is an artist
    if is_potential_artist_query(user_message):
        artist_info = check_if_artist_exists(user_message.strip(), spotify)
        if artist_info:
            print(f"🎯 Dynamic artist detection successful: {artist_info['name']}")
            return {
                'type': 'artist_search',
                'artist_name': artist_info['name'],
                'artist_id': artist_info['id'],
                'search_terms': [f"{artist_info['name']} songs", f"{artist_info['name']} popular", f"{artist_info['name']} hits"],
                'genre_hint': f'songs by {artist_info["name"]}'
            }
    # Add this section RIGHT AFTER your dynamic artist detection and BEFORE Bengali music detection:

    # 🎭 GENRE COMBINATIONS - Check for mood + region/genre combinations
    
    # Happy combinations
    if 'happy' in message_lower and 'bollywood' in message_lower:
        return {
            'type': 'happy_bollywood',
            'search_terms': [
                'happy bollywood songs', 'upbeat hindi music', 'bollywood dance',
                'cheerful hindi', 'joyful bollywood', 'bollywood party songs'
            ],
            'genre_hint': 'happy Bollywood music'
        }
    
    elif 'happy' in message_lower and any(word in message_lower for word in ['kpop', 'k-pop', 'korean']):
        return {
            'type': 'happy_kpop',
            'search_terms': [
                'happy kpop', 'upbeat korean songs', 'cheerful kpop',
                'bts happy songs', 'twice upbeat', 'kpop dance songs'
            ],
            'genre_hint': 'happy K-pop music'
        }
    
    elif 'happy' in message_lower and any(word in message_lower for word in ['afrobeats', 'african']):
        return {
            'type': 'happy_afrobeats',
            'search_terms': [
                'happy afrobeats', 'upbeat african music', 'joyful afrobeats',
                'afrobeats dance', 'cheerful nigerian music', 'party afrobeats'
            ],
            'genre_hint': 'happy Afrobeats music'
        }
    
    elif 'happy' in message_lower and 'latin' in message_lower:
        return {
            'type': 'happy_latin',
            'search_terms': [
                'happy latin music', 'upbeat reggaeton', 'joyful salsa',
                'latin dance songs', 'cheerful spanish music', 'party latin'
            ],
            'genre_hint': 'happy Latin music'
        }
    
    # Sad combinations
    elif 'sad' in message_lower and 'bollywood' in message_lower:
        return {
            'type': 'sad_bollywood',
            'search_terms': [
                'sad bollywood songs', 'emotional hindi music', 'bollywood heartbreak',
                'melancholic hindi', 'sad arijit singh', 'bollywood breakup songs'
            ],
            'genre_hint': 'sad Bollywood music'
        }
    
    elif 'sad' in message_lower and any(word in message_lower for word in ['kpop', 'k-pop', 'korean']):
        return {
            'type': 'sad_kpop',
            'search_terms': [
                'sad kpop', 'emotional korean songs', 'melancholic kpop',
                'bts sad songs', 'iu emotional', 'kpop ballads'
            ],
            'genre_hint': 'sad K-pop music'
        }
    
    elif 'sad' in message_lower and 'indie' in message_lower:
        return {
            'type': 'sad_indie',
            'search_terms': [
                'sad indie music', 'melancholic indie', 'emotional indie rock',
                'indie heartbreak', 'sad alternative', 'indie folk sad'
            ],
            'genre_hint': 'sad indie music'
        }
    
    # Chill combinations
    elif 'chill' in message_lower and any(word in message_lower for word in ['kpop', 'k-pop', 'korean']):
        return {
            'type': 'chill_kpop',
            'search_terms': [
                'chill kpop', 'relaxing korean music', 'calm kpop',
                'lofi kpop', 'chill korean r&b', 'peaceful kpop'
            ],
            'genre_hint': 'chill K-pop music'
        }
    
    elif 'chill' in message_lower and 'bollywood' in message_lower:
        return {
            'type': 'chill_bollywood',
            'search_terms': [
                'chill bollywood', 'relaxing hindi music', 'calm bollywood',
                'peaceful hindi songs', 'bollywood acoustic', 'soft bollywood'
            ],
            'genre_hint': 'chill Bollywood music'
        }
    
    elif 'chill' in message_lower and 'afrobeats' in message_lower:
        return {
            'type': 'chill_afrobeats',
            'search_terms': [
                'chill afrobeats', 'relaxing african music', 'smooth afrobeats',
                'calm nigerian music', 'afrobeats r&b', 'mellow afrobeats'
            ],
            'genre_hint': 'chill Afrobeats music'
        }
    
    # Energetic combinations
    elif any(word in message_lower for word in ['energetic', 'pump', 'hype', 'intense']) and 'bollywood' in message_lower:
        return {
            'type': 'energetic_bollywood',
            'search_terms': [
                'energetic bollywood', 'pump up hindi songs', 'high energy bollywood',
                'bollywood workout songs', 'intense hindi music', 'hype bollywood'
            ],
            'genre_hint': 'energetic Bollywood music'
        }
    
    elif any(word in message_lower for word in ['energetic', 'pump', 'hype', 'intense']) and any(word in message_lower for word in ['kpop', 'k-pop']):
        return {
            'type': 'energetic_kpop',
            'search_terms': [
                'energetic kpop', 'pump up korean songs', 'high energy kpop',
                'kpop workout songs', 'intense kpop', 'hype korean music'
            ],
            'genre_hint': 'energetic K-pop music'
        }
    
    # Romantic combinations
    elif any(word in message_lower for word in ['romantic', 'love']) and 'bollywood' in message_lower:
        return {
            'type': 'romantic_bollywood',
            'search_terms': [
                'romantic bollywood songs', 'love hindi music', 'bollywood romantic',
                'hindi love songs', 'romantic arijit singh', 'bollywood couples songs'
            ],
            'genre_hint': 'romantic Bollywood music'
        }
    
    elif any(word in message_lower for word in ['romantic', 'love']) and any(word in message_lower for word in ['kpop', 'k-pop']):
        return {
            'type': 'romantic_kpop',
            'search_terms': [
                'romantic kpop', 'love korean songs', 'kpop love ballads',
                'romantic korean music', 'kpop couples songs', 'korean love songs'
            ],
            'genre_hint': 'romantic K-pop music'
        }
 
    # 🇧🇩 BENGALI MUSIC (SEPARATE from Hindi/Bollywood!)
    if any(word in message_lower for word in ['bengali', 'bangla', 'bengali song', 'bengali music', 'bangladesh music']):
        return {
            'type': 'bengali',
            'search_terms': [
                'bengali songs', 'bangla music', 'bengali folk', 'bengali modern',
                'rabindra sangeet', 'nazrul geeti', 'bengali romantic', 'bengali sad',
                'kishore kumar bengali', 'lata mangeshkar bengali', 'hemanta mukherjee',
                'manna dey bengali', 'sandhya mukherjee', 'shyama sangeet',
                'bengali adhunik gan', 'bengali basic', 'bengali movie songs',
                'calcutta bengali', 'dhaka bengali', 'bengali classical',
                'bengali devotional', 'durga puja songs', 'kali puja songs',
                'poila boishakh songs', 'bengali new year', 'bangla band',
                'fossils band', 'cactus band', 'chandrabindoo', 'bhoomi band'
            ],
            'genre_hint': 'Bengali and Bangla music'
        }
    
    # 🇮🇳 TAMIL MUSIC (SEPARATE category!)
    elif any(word in message_lower for word in ['tamil', 'tamil song', 'tamil music', 'kollywood', 'chennai music']):
        return {
            'type': 'tamil',
            'search_terms': [
                'tamil songs', 'kollywood music', 'tamil movie songs', 'tamil folk',
                'a r rahman tamil', 'ilaiyaraaja', 'harris jayaraj', 'anirudh ravichander',
                'yuvan shankar raja', 'tamil romantic', 'tamil melody', 'tamil kuthu',
                'tamil classical', 'carnatic music', 'tamil devotional', 'murugan songs',
                'tamil gaana', 'chennai gana', 'tamil rap', 'hip hop tamizha',
                'tamil independent', 'tamil indie', 'thalapathy songs', 'ajith songs',
                'suriya songs', 'dhanush songs', 'tamil latest', 'tamil hits'
            ],
            'genre_hint': 'Tamil and Kollywood music'
        }
    
    # 🇮🇳 TELUGU MUSIC (SEPARATE category!)
    elif any(word in message_lower for word in ['telugu', 'telugu song', 'telugu music', 'tollywood', 'hyderabad music']):
        return {
            'type': 'telugu',
            'search_terms': [
                'telugu songs', 'tollywood music', 'telugu movie songs', 'telugu folk',
                'devi sri prasad', 'thaman', 'mickey j meyer', 'gopi sundar telugu',
                'telugu romantic', 'telugu melody', 'telugu mass', 'telugu classical',
                'annamayya songs', 'tyagaraja kritis telugu', 'telugu devotional',
                'telugu folk songs', 'telugu village songs', 'telugu indie',
                'pawan kalyan songs', 'mahesh babu songs', 'ram charan songs',
                'allu arjun songs', 'jr ntr songs', 'telugu latest', 'telugu hits'
            ],
            'genre_hint': 'Telugu and Tollywood music'
        }
    
    # 🇮🇳 PUNJABI MUSIC (SEPARATE category!)
    elif any(word in message_lower for word in ['punjabi', 'punjabi song', 'punjabi music', 'bhangra', 'punjab music']):
        return {
            'type': 'punjabi',
            'search_terms': [
                'punjabi songs', 'bhangra music', 'punjabi folk', 'punjabi pop',
                'diljit dosanjh', 'gurdas maan', 'babbu maan', 'ammy virk',
                'hardy sandhu', 'guru randhawa', 'sidhu moose wala', 'karan aujla',
                'punjabi romantic', 'punjabi sad', 'punjabi party', 'punjabi dhol',
                'punjabi classical', 'gurbani', 'punjabi devotional', 'punjabi rap',
                'punjabi hip hop', 'punjabi indie', 'punjabi latest', 'punjabi hits',
                'pollywood music', 'punjabi movie songs', 'sufi punjabi'
            ],
            'genre_hint': 'Punjabi and Bhangra music'
        }
    
    # 🌍 AFROBEATS & AFRICAN MUSIC (SEPARATE and ENHANCED!)
    elif any(word in message_lower for word in ['afrobeats', 'afro beats', 'african', 'nigerian', 'ghana music', 'afro music', 'african song']):
        return {
            'type': 'afrobeats',
            'search_terms': [
                'afrobeats', 'afro beats', 'nigerian music', 'ghana music', 'african music',
                'burna boy', 'wizkid', 'davido', 'tiwa savage', 'yemi alade',
                'mr eazi', 'tekno', 'runtown', 'patoranking', 'stonebwoy',
                'shatta wale', 'sarkodie', 'kcee', 'flavour', 'phyno',
                'afro pop', 'afro fusion', 'afro trap', 'afro house', 'amapiano',
                'highlife', 'juju music', 'fuji music', 'african drums',
                'west african music', 'east african music', 'south african music',
                'kenyan music', 'ethiopian music', 'congolese music', 'soukous'
            ],
            'genre_hint': 'Afrobeats and African music'
        }
    
    # 🇰🇪 KENYAN & EAST AFRICAN
    elif any(word in message_lower for word in ['kenyan', 'kenya music', 'east african', 'swahili music', 'bongo flava']):
        return {
            'type': 'east_african',
            'search_terms': [
                'kenyan music', 'bongo flava', 'swahili music', 'east african music',
                'diamond platnumz', 'rayvanny', 'harmonize', 'ali kiba', 'vanessa mdee',
                'sauti sol', 'akothee', 'bahati', 'willy paul', 'nyashinski',
                'tanzanian music', 'ugandan music', 'rwandan music', 'ethiopian music',
                'amharic music', 'oromo music', 'taarab music', 'benga music',
                'kapuka music', 'genge music', 'afro zoom', 'singeli'
            ],
            'genre_hint': 'East African and Swahili music'
        }
    
    # 🇯🇲 REGGAE & CARIBBEAN (ENHANCED!)
    elif any(word in message_lower for word in ['reggae', 'jamaican', 'caribbean', 'dancehall', 'soca', 'calypso']):
        return {
            'type': 'caribbean',
            'search_terms': [
                'reggae music', 'jamaican music', 'caribbean music', 'dancehall',
                'bob marley', 'jimmy cliff', 'toots hibbert', 'burning spear',
                'shaggy', 'sean paul', 'beenie man', 'bounty killer', 'vybz kartel',
                'chronixx', 'protoje', 'koffee', 'spice dancehall', 'popcaan',
                'soca music', 'calypso music', 'trinidad music', 'barbados music',
                'steel drum', 'carnival music', 'mento music', 'ska music',
                'rocksteady', 'roots reggae', 'dub music', 'ragga music'
            ],
            'genre_hint': 'Reggae and Caribbean music'
        }
    
    # 🇧🇷 BRAZILIAN MUSIC (SEPARATE!)
    elif any(word in message_lower for word in ['brazilian', 'brazil music', 'portuguese music', 'bossa nova', 'samba', 'forró']):
        return {
            'type': 'brazilian',
            'search_terms': [
                'brazilian music', 'bossa nova', 'samba', 'forró', 'mpb',
                'anitta', 'ludmilla', 'wesley safadão', 'gusttavo lima', 'marília mendonça',
                'caetano veloso', 'gilberto gil', 'chico buarque', 'maria bethânia',
                'tropicália', 'axé music', 'pagode', 'funk carioca', 'brazilian funk',
                'sertanejo', 'brazilian pop', 'brazilian rock', 'brazilian hip hop',
                'baião', 'frevo', 'choro', 'maracatu', 'lambada'
            ],
            'genre_hint': 'Brazilian and Portuguese music'
        }
    
    # 🇮🇳 HINDI/BOLLYWOOD (KEEP SEPARATE!)
    elif any(word in message_lower for word in ['hindi', 'bollywood', 'indian music', 'hindi song']):
        return {
            'type': 'hindi_bollywood',
            'search_terms': [
                'bollywood music', 'hindi songs', 'hindi movie songs', 'bollywood hits',
                'a r rahman', 'arijit singh', 'shreya ghoshal', 'lata mangeshkar',
                'kishore kumar', 'mohammed rafi', 'asha bhosle', 'sonu nigam',
                'atif aslam', 'rahat fateh ali khan', 'mohit chauhan', 'armaan malik',
                'sunidhi chauhan', 'shaan', 'kk singer', 'udit narayan',
                'hindi romantic songs', 'bollywood dance', 'hindi pop',
                'indian classical', 'qawwali', 'devotional hindi', 'bollywood old',
                'bollywood new', 'hindi indie', 'bollywood item songs'
            ],
            'genre_hint': 'Hindi Bollywood music'
        }
    
    # 🇯🇵 JAPANESE & ANIME (existing)
    elif any(word in message_lower for word in ['anime', 'japanese', 'jpop', 'j-pop', 'otaku', 'weeb', 'manga']):
        return {
            'type': 'anime_japanese',
            'search_terms': [
                'japanese anime opening', 'anime soundtrack', 'jpop', 'japanese music',
                'j-rock', 'japanese electronic', 'anime ost', 'naruto opening',
                'studio ghibli', 'japanese indie', 'visual kei', 'shibuya-kei',
                'japanese punk', 'japanese metal', 'vocaloid', 'japanese folk'
            ],
            'genre_hint': 'Japanese anime or J-pop music'
        }
    elif any(word in message_lower for word in ['kpop', 'k-pop', 'korean', 'bts', 'blackpink', 'twice']):
        return {
            'type': 'kpop',
            'search_terms': [
                'kpop', 'korean pop', 'korean music', 'k-indie', 'korean rock',
                'korean hip hop', 'korean ballad', 'korean electronic', 'korean r&b',
                'korean folk', 'korean alternative', 'korean punk', 'k-rock'
            ],
            'genre_hint': 'K-pop or Korean music'
        }
    elif any(word in message_lower for word in ['rock', 'metal', 'punk', 'grunge', 'alternative']):
        return {
            'type': 'rock',
            'search_terms': [
                'rock music', 'alternative rock', 'indie rock', 'classic rock',
                'progressive rock', 'punk rock', 'grunge', 'post-rock',
                'metal', 'hard rock', 'soft rock', 'psychedelic rock',
                'garage rock', 'folk rock', 'blues rock', 'arena rock'
            ],
            'genre_hint': 'rock music'
        }
    elif any(word in message_lower for word in ['rap', 'hip hop', 'hip-hop', 'trap', 'drill']):
        return {
            'type': 'hiphop',
            'search_terms': [
                'hip hop', 'rap music', 'hip-hop', 'trap music', 'drill rap',
                'old school hip hop', 'conscious rap', 'gangsta rap', 'mumble rap',
                'underground hip hop', 'boom bap', 'trap beats', 'rap battles',
                'freestyle rap', 'east coast rap', 'west coast rap', 'southern rap'
            ],
            'genre_hint': 'hip-hop or rap music'
        }
    elif any(word in message_lower for word in ['pop', 'mainstream', 'radio', 'chart', 'hits']):
        return {
            'type': 'pop',
            'search_terms': [
                'pop music', 'mainstream pop', 'indie pop', 'synth pop', 'dance pop',
                'electropop', 'pop rock', 'teen pop', 'adult contemporary',
                'power pop', 'art pop', 'chamber pop', 'dream pop', 'pop punk'
            ],
            'genre_hint': 'pop music'
        }
    elif any(word in message_lower for word in ['electronic', 'edm', 'techno', 'house', 'dubstep']):
        return {
            'type': 'electronic',
            'search_terms': [
                'electronic music', 'edm', 'techno', 'house music', 'dubstep',
                'trance', 'drum and bass', 'ambient electronic', 'chillwave',
                'synthwave', 'future bass', 'deep house', 'progressive house',
                'electro house', 'minimal techno', 'acid house', 'breakbeat'
            ],
            'genre_hint': 'electronic and dance music'
        }
    
    # 🎵 NICHE GENRES (existing)
    elif any(word in message_lower for word in ['post-rock', 'post rock', 'instrumental rock', 'epic instrumental']):
        return {
            'type': 'post_rock',
            'search_terms': [
                'post-rock', 'instrumental rock', 'epic instrumental', 'cinematic rock',
                'godspeed you black emperor', 'explosions in the sky', 'this will destroy you',
                'mono', 'russian circles', 'sigur ros', 'epic guitar', 'atmospheric rock'
            ],
            'genre_hint': 'post-rock and epic instrumental music'
        }
    elif any(word in message_lower for word in ['ambient', 'atmospheric', 'soundscape', 'drone', 'minimal']):
        return {
            'type': 'ambient',
            'search_terms': [
                'ambient music', 'atmospheric music', 'drone music', 'soundscape',
                'brian eno', 'tim hecker', 'william basinski', 'stars of the lid',
                'minimal ambient', 'dark ambient', 'field recordings', 'sound art',
                'new age', 'meditation music', 'space music', 'ethereal ambient'
            ],
            'genre_hint': 'ambient and atmospheric music'
        }
    elif any(word in message_lower for word in ['shoegaze', 'dream pop', 'ethereal', 'wall of sound']):
        return {
            'type': 'shoegaze',
            'search_terms': [
                'shoegaze', 'dream pop', 'my bloody valentine', 'slowdive', 'ride',
                'cocteau twins', 'beach house', 'mazzy star', 'ethereal wave',
                'noise pop', 'wall of sound', 'reverb heavy', 'atmospheric pop'
            ],
            'genre_hint': 'shoegaze and dream pop music'
        }
    
    # 🌟 MAINSTREAM HITS (existing)
    elif any(word in message_lower for word in ['mainstream', 'chart hits', 'billboard', 'radio hits', 'viral']):
        return {
            'type': 'mainstream',
            'search_terms': [
                'taylor swift', 'drake', 'billie eilish', 'post malone', 'ariana grande',
                'the weeknd', 'dua lipa', 'olivia rodrigo', 'harry styles', 'bad bunny',
                'chart hits', 'billboard top', 'mainstream pop', 'radio hits', 'viral hits',
                'trending songs', 'popular music', 'hit songs', 'top 40'
            ],
            'genre_hint': 'mainstream hits and chart toppers'
        }
    
    # 🎨 INDIE DISCOVERIES (existing)
    elif any(word in message_lower for word in ['indie', 'underground', 'alternative', 'experimental', 'art rock']):
        return {
            'type': 'indie',
            'search_terms': [
                'phoebe bridgers', 'tame impala', 'mac miller', 'clairo', 'boy pablo',
                'rex orange county', 'beach house', 'vampire weekend', 'arctic monkeys',
                'indie rock', 'indie pop', 'indie folk', 'indie electronic', 'bedroom pop',
                'dream pop', 'art rock', 'experimental indie', 'lo-fi indie', 'indie sleaze'
            ],
            'genre_hint': 'indie and alternative discoveries'
        }
    
    # 📅 DECADES (existing)
    elif any(word in message_lower for word in ['70s', '1970s', 'seventies', 'disco era', 'classic rock era']):
        return {
            'type': 'seventies',
            'search_terms': [
                '70s hits', '1970s music', 'seventies', 'disco music', 'classic rock 70s',
                'funk 70s', 'soul 70s', 'psychedelic rock', 'progressive rock 70s',
                'folk rock 70s', 'hard rock 70s', 'glam rock', 'punk 70s', 'reggae 70s'
            ],
            'genre_hint': '1970s music and disco era hits'
        }
    elif any(word in message_lower for word in ['80s', '1980s', 'eighties', 'new wave', 'synth pop']):
        return {
            'type': 'eighties',
            'search_terms': [
                '80s hits', '1980s music', 'eighties', 'new wave', 'synth pop',
                'post-punk', 'new romantic', 'hair metal', 'glam metal', 'freestyle',
                'electronic 80s', 'pop rock 80s', 'alternative 80s', 'dance 80s'
            ],
            'genre_hint': '1980s new wave and synth pop'
        }
    elif any(word in message_lower for word in ['90s', '1990s', 'nineties', 'grunge', 'alternative rock']):
        return {
            'type': 'nineties',
            'search_terms': [
                '90s hits', '1990s music', 'nineties', 'grunge', 'alternative rock 90s',
                'britpop', 'trip-hop', 'electronic 90s', 'hip hop 90s', 'r&b 90s',
                'indie rock 90s', 'shoegaze 90s', 'post-rock 90s', 'rave music'
            ],
            'genre_hint': '1990s grunge and alternative rock'
        }
    elif any(word in message_lower for word in ['2000s', 'early 2000s', 'y2k', 'millennium', 'emo']):
        return {
            'type': 'two_thousands',
            'search_terms': [
                '2000s hits', 'early 2000s', 'y2k music', 'millennium music', 'emo',
                'pop punk 2000s', 'nu metal', 'garage rock revival', 'crunk',
                'teen pop 2000s', 'r&b 2000s', 'indie rock 2000s', 'post-hardcore'
            ],
            'genre_hint': '2000s emo and pop punk era'
        }
    
    # 😊 POSITIVE EMOTIONS (existing)
    elif any(word in message_lower for word in ['happy', 'joyful', 'cheerful', 'sunny', 'upbeat', 'good mood']):
        return {
            'type': 'happy',
            'search_terms': [
                'happy songs', 'feel good music', 'upbeat pop', 'cheerful music',
                'joyful indie', 'sunny reggae', 'happy folk', 'uplifting soul',
                'positive vibes', 'good mood rock', 'happy electronic', 'cheerful jazz',
                'feel good hip hop', 'happy country', 'upbeat latin', 'joyful gospel'
            ],
            'genre_hint': 'happy and uplifting music'
        }
    elif any(word in message_lower for word in ['excited', 'thrilled', 'pumped', 'hyped', 'stoked', 'energetic']):
        return {
            'type': 'excited',
            'search_terms': [
                'pump up songs', 'hype music', 'energetic pop', 'party anthems',
                'high energy rock', 'intense electronic', 'adrenaline music',
                'workout songs', 'explosive beats', 'epic music', 'power anthems',
                'motivational rock', 'intense rap', 'high tempo', 'festival bangers'
            ],
            'genre_hint': 'exciting and energetic music'
        }
    elif any(word in message_lower for word in ['love', 'romantic', 'affectionate', 'passionate', 'tender', 'romance']):
        return {
            'type': 'romantic',
            'search_terms': [
                'love songs', 'romantic ballads', 'slow jams', 'romantic music',
                'love ballads', 'romantic pop', 'romantic rock', 'romantic r&b',
                'acoustic love songs', 'romantic indie', 'love duets', 'romantic jazz',
                'romantic soul', 'romantic country', 'romantic folk', 'serenades'
            ],
            'genre_hint': 'romantic and love songs'
        }
    elif any(word in message_lower for word in ['confident', 'empowered', 'strong', 'bold', 'powerful', 'badass']):
        return {
            'type': 'confident',
            'search_terms': [
                'empowerment anthems', 'confidence boosters', 'powerful songs', 'boss music',
                'strong female vocals', 'empowering hip hop', 'confident pop', 'bold rock',
                'powerful ballads', 'badass songs', 'strong anthems', 'fierce music'
            ],
            'genre_hint': 'confident and empowering music'
        }
    elif any(word in message_lower for word in ['grateful', 'thankful', 'appreciative', 'blessed']):
        return {
            'type': 'grateful',
            'search_terms': [
                'grateful songs', 'thankful music', 'appreciation anthems', 'blessing songs',
                'gratitude music', 'thankful folk', 'grateful rock', 'appreciation pop'
            ],
            'genre_hint': 'grateful and appreciative music'
        }
    elif any(word in message_lower for word in ['peaceful', 'calm', 'serene', 'tranquil', 'chill', 'relaxed']):
        return {
            'type': 'peaceful',
            'search_terms': [
                'chill music', 'relaxing songs', 'peaceful acoustic', 'ambient chill',
                'calm electronic', 'serene folk', 'tranquil jazz', 'peaceful piano',
                'relaxing indie', 'chill hip hop', 'peaceful classical', 'calm pop'
            ],
            'genre_hint': 'peaceful and calming music'
        }
    
    # 😔 NEGATIVE EMOTIONS (existing)
    elif any(word in message_lower for word in ['sad', 'melancholic', 'sorrowful', 'heartbroken', 'depressed', 'down']):
        return {
            'type': 'sad',
            'search_terms': [
                'sad songs', 'melancholic music', 'heartbreak ballads', 'emotional songs',
                'depressing music', 'sad indie', 'melancholy folk', 'sad acoustic',
                'breakup songs', 'crying songs', 'sad piano', 'emotional ballads',
                'sad alternative', 'melancholic electronic', 'sad country', 'blues music'
            ],
            'genre_hint': 'sad and emotional music'
        }
    elif any(word in message_lower for word in ['angry', 'furious', 'aggressive', 'mad', 'rage', 'pissed']):
        return {
            'type': 'angry',
            'search_terms': [
                'angry music', 'aggressive rock', 'metal songs', 'rage music',
                'hardcore punk', 'angry rap', 'aggressive electronic', 'thrash metal',
                'nu metal', 'angry alternative', 'hardcore music', 'intense rock',
                'angry hip hop', 'aggressive indie', 'punk rock', 'death metal'
            ],
            'genre_hint': 'angry and aggressive music'
        }
    elif any(word in message_lower for word in ['anxious', 'worried', 'nervous', 'stressed', 'anxiety', 'panic']):
        return {
            'type': 'anxious',
            'search_terms': [
                'calming music', 'anxiety relief songs', 'soothing tracks', 'stress relief',
                'peaceful ambient', 'relaxing classical', 'calming indie', 'soothing folk'
            ],
            'genre_hint': 'calming music for anxiety relief'
        }
    elif any(word in message_lower for word in ['lonely', 'isolated', 'empty', 'longing', 'alone']):
        return {
            'type': 'lonely',
            'search_terms': [
                'lonely songs', 'isolation music', 'longing ballads', 'alone time tracks',
                'solitude music', 'lonely indie', 'melancholy folk', 'isolation rock'
            ],
            'genre_hint': 'music for lonely moments'
        }
    
    # 🌍 LATIN MUSIC (enhanced existing)
    elif any(word in message_lower for word in ['latin', 'spanish', 'reggaeton', 'salsa', 'bachata']):
        return {
            'type': 'latin',
            'search_terms': [
                'latin music', 'reggaeton', 'salsa', 'bachata', 'spanish music',
                'merengue', 'cumbia', 'latin pop', 'spanish rock', 'latin hip hop',
                'flamenco', 'bossa nova', 'samba', 'tango', 'mariachi', 'latin jazz'
            ],
            'genre_hint': 'Latin and Spanish music'
        }
    
    # 🎭 ACTIVITY-BASED (existing)
    elif any(word in message_lower for word in ['workout', 'gym', 'cardio', 'strength', 'exercise', 'fitness']):
        return {
            'type': 'workout',
            'search_terms': [
                'workout music', 'gym songs', 'cardio tracks', 'fitness anthems',
                'running music', 'weightlifting songs', 'exercise music', 'training beats',
                'high energy workout', 'intense fitness', 'power training', 'HIIT music',
                'crossfit music', 'spinning music', 'marathon music', 'athletic anthems'
            ],
            'genre_hint': 'workout and fitness music'
        }
    elif any(word in message_lower for word in ['study', 'focus', 'concentration', 'work', 'productive']):
        return {
            'type': 'study',
            'search_terms': [
                'study music', 'focus tracks', 'concentration songs', 'productive vibes',
                'ambient study', 'lo-fi hip hop', 'classical study', 'peaceful instrumental',
                'brain music', 'meditation music', 'white noise', 'nature sounds',
                'minimal electronic', 'study beats', 'calm piano', 'reading music'
            ],
            'genre_hint': 'study and focus music'
        }
    elif any(word in message_lower for word in ['party', 'celebration', 'dance', 'social', 'club']):
        return {
            'type': 'party',
            'search_terms': [
                'party music', 'dance songs', 'celebration tracks', 'club anthems',
                'party bangers', 'dance hits', 'club music', 'party pop',
                'festival music', 'dance floor', 'party rock', 'upbeat dance',
                'party hip hop', 'dance electronic', 'party classics', 'celebration songs'
            ],
            'genre_hint': 'party and dance music'
        }
    elif any(word in message_lower for word in ['driving', 'road trip', 'cruising', 'car', 'highway']):
        return {
            'type': 'driving',
            'search_terms': [
                'driving music', 'road trip songs', 'cruising tracks', 'highway anthems',
                'car music', 'travel songs', 'journey music', 'road music'
            ],
            'genre_hint': 'driving and road trip music'
        }
    
    # 🎮 MODERN CATEGORIES (existing)
    elif any(word in message_lower for word in ['gaming', 'games', 'video game', 'epic', 'boss battle', 'rpg']):
        return {
            'type': 'gaming',
            'search_terms': [
                'gaming music', 'epic electronic', 'video game soundtracks', 'boss battle',
                'epic orchestral', 'cinematic music', 'dramatic electronic', 'intense gaming',
                'rpg music', 'fantasy music', 'adventure music', 'heroic music',
                'epic trailer music', 'powerful orchestral', 'dramatic scores'
            ],
            'genre_hint': 'gaming and epic music'
        }
    elif any(word in message_lower for word in ['lofi', 'lo-fi', 'chill hop', 'study beats', 'aesthetic']):
        return {
            'type': 'lofi',
            'search_terms': [
                'lo-fi hip hop', 'chill hop', 'study beats', 'lofi music',
                'aesthetic music', 'chillwave', 'lo-fi beats', 'relaxing hip hop',
                'calm beats', 'peaceful hip hop', 'ambient hip hop', 'dreamy beats',
                'nostalgic beats', 'vintage hip hop', 'soft beats', 'mellow hip hop'
            ],
            'genre_hint': 'lo-fi and chill hop music'
        }
    elif any(word in message_lower for word in ['vietnamese', 'vietnam music', 'vpop', 'vietnamese song']):
        return {
            'type': 'vietnamese',
            'search_terms': [
                'vietnamese music', 'vpop', 'vietnam pop', 'vietnamese songs',
                'son tung mtp', 'duc phuc', 'erik vietnam', 'chi pu',
                'vietnamese ballad', 'vietnamese rap', 'vietnamese indie',
                'vietnamese folk', 'vietnamese modern', 'ho chi minh music'
            ],
            'genre_hint': 'Vietnamese and V-pop music'
        }
    
    # 🇹🇭 THAI MUSIC
    elif any(word in message_lower for word in ['thai', 'thailand music', 'thai song', 'thai pop']):
        return {
            'type': 'thai',
            'search_terms': [
                'thai music', 'thai pop', 'thailand songs', 'thai ballad',
                'bodyslam', 'potato', 'clash', 'silly fools', 'big ass',
                'thai indie', 'thai rock', 'thai hip hop', 'thai folk',
                'luk thung', 'mor lam', 'thai country', 'bangkok music'
            ],
            'genre_hint': 'Thai music and T-pop'
        }
    
    # 🇸🇦 ARABIC & MIDDLE EASTERN MUSIC
    elif any(word in message_lower for word in ['arabic', 'middle eastern', 'arabic music', 'arab music', 'lebanese', 'egyptian music']):
        return {
            'type': 'arabic',
            'search_terms': [
                'arabic music', 'middle eastern music', 'arab songs',
                'fairuz', 'amr diab', 'nancy ajram', 'elissa', 'tamer hosny',
                'arabic pop', 'arabic classical', 'oud music', 'arabic ballad',
                'egyptian music', 'lebanese music', 'iraqi music', 'syrian music',
                'arabic rap', 'arabic folk', 'traditional arabic'
            ],
            'genre_hint': 'Arabic and Middle Eastern music'
        }
    
    # 🇮🇩 INDONESIAN MUSIC
    elif any(word in message_lower for word in ['indonesian', 'indonesia music', 'indo music', 'indonesian song']):
        return {
            'type': 'indonesian',
            'search_terms': [
                'indonesian music', 'indo pop', 'indonesia songs',
                'raisa', 'isyana sarasvati', 'afgan', 'glenn fredly',
                'indonesian indie', 'indonesian rock', 'dangdut',
                'indonesian folk', 'jakarta music', 'indonesian ballad'
            ],
            'genre_hint': 'Indonesian music and Indo-pop'
        }
    
    # 🇫🇮 FINNISH & NORDIC MUSIC
    elif any(word in message_lower for word in ['finnish', 'finland music', 'nordic music', 'scandinavian music']):
        return {
            'type': 'nordic',
            'search_terms': [
                'finnish music', 'nordic music', 'scandinavian music',
                'sunrise avenue', 'nightwish', 'him band', 'children of bodom',
                'finnish rock', 'nordic folk', 'finnish metal', 'nordic pop',
                'icelandic music', 'norwegian music', 'danish music', 'swedish indie'
            ],
            'genre_hint': 'Finnish and Nordic music'
        }
    
    # 🇲🇽 MEXICAN & REGIONAL MEXICAN
    elif any(word in message_lower for word in ['mexican', 'mexico music', 'mariachi', 'banda', 'ranchera']):
        return {
            'type': 'mexican',
            'search_terms': [
                'mexican music', 'mariachi', 'banda music', 'ranchera',
                'vicente fernandez', 'juan gabriel', 'alejandro fernandez',
                'mexican folk', 'regional mexican', 'norteño', 'corridos',
                'mexican pop', 'mexican rock', 'mexican indie', 'mexico traditional'
            ],
            'genre_hint': 'Mexican and Regional Mexican music'
        }
    
    # 🇷🇺 RUSSIAN & EASTERN EUROPEAN
    elif any(word in message_lower for word in ['russian', 'russia music', 'eastern european', 'slavic music']):
        return {
            'type': 'russian',
            'search_terms': [
                'russian music', 'russian pop', 'russian rock',
                'russian folk', 'eastern european music', 'slavic music',
                'russian ballad', 'russian indie', 'soviet music',
                'ukrainian music', 'polish music', 'czech music'
            ],
            'genre_hint': 'Russian and Eastern European music'
        }
    
    # 🎵 DEFAULT CASE
    else:
        return {
            'type': 'general',
            'search_terms': [
                'popular music', 'trending songs', 'chart hits', 'radio hits',
                'viral songs', 'new releases', 'indie hits', 'underground hits',
                'international hits', 'crossover hits', 'breakthrough artists',
                'emerging artists', 'hidden gems', 'cult classics', 'fan favorites'
            ],
            'genre_hint': 'diverse popular music from around the world'
        }

def generate_ai_response(user_message, user_request, available_songs, suggested_songs):
    """Generate AI response using Gemini - FIXED ARTIST SEARCH LOGIC"""
    
    # Create the song list for AI prompt
    if available_songs:
        songs_list = "\n".join([f"- {song}" for song in available_songs[:20]])
    else:
        songs_list = "No matching songs found in database"
    
    # 🧠 MEMORY: Create exclusion list for AI
    exclusion_text = ""
    if suggested_songs:
        exclusion_text = f"""

🚨🚨🚨 CRITICAL MEMORY RULE - ABSOLUTELY NEVER suggest these songs (already suggested):
{chr(10).join([f"❌ {song}" for song in suggested_songs])}

⚠️ IF YOU SUGGEST ANY OF THE ABOVE SONGS, THE SYSTEM WILL BREAK!
✅ YOU MUST suggest a COMPLETELY DIFFERENT song from the available list above!
🔄 Memory check: {len(suggested_songs)} songs already suggested - pick something NEW!"""

    # 🎯 SPECIFIC SONG SEARCH
    if user_request['type'] == 'specific_song':
        song_name = user_request['song_name']
        artist_name = user_request['artist_name']
        prompt = f"""You are YAIN! The user wants "{song_name}" by {artist_name}.
    
        Respond excitedly and suggest exactly: Try '{song_name}' by {artist_name}
    
        Your response:"""
    
    # 🎤 ARTIST SEARCH (UPDATED - including dynamic detection)
    elif user_request['type'] == 'artist_search':
        artist_name = user_request['artist_name']
        artist_id = user_request.get('artist_id')  # May be provided by dynamic detection
        prompt = f"""You are YAIN! The user wants songs by {artist_name}.
    
        Available songs by {artist_name}:
        {songs_list}
    
        Pick ONE song from the list above and be excited about {artist_name}!
        Format: Try 'Song Name' by Artist Name
        
        {exclusion_text}
    
        Your response:"""
    
    # 🎭 GENERAL REQUESTS (existing logic - UNCHANGED)
    else:
        prompt = f"""
You are YAIN, a cheeky, witty music chatbot with personality! You're like that friend who always knows the perfect song and loves to chat.

User said: "{user_message}"

Your response should:
1. First, respond to what they said in a clever, funny, or encouraging way (like a friend would)
2. Reference a song theme naturally in your conversation 
3. Then suggest that specific song with "Try 'Song Name' by Artist Name"


Examples of your conversational style:
"Oof, sounds like you're all stressed out! Life's been hitting different lately, huh? 😅 Try 'Stressed Out' by Twenty One Pilots!"

"Bengali vibes incoming! 🇧🇩 Those soulful melodies are about to transport you! Try 'Ei Raat Tomar Amar' by Kishore Kumar!"

WHAT THEY WANT: {user_request['genre_hint']}

AVAILABLE SONGS FOR THIS REQUEST:
{songs_list}
{exclusion_text}

INSTRUCTIONS:
- Be conversational and friendly first, then suggest music
- Use emojis naturally (not excessively) 
- React to their mood genuinely
- Pick ONE song from the available list above
- Format as: "Try 'Song Name' by Artist Name"
- ⚠️ NEVER EVER repeat songs from the exclusion list above
- 🧠 MEMORY: You have suggested {len(suggested_songs)} songs before - pick something COMPLETELY different!
- Keep it engaging but not too long

🔄 MEMORY CHECK: Avoid all {len(suggested_songs)} previously suggested songs above!

Your conversational response (chat first, then suggest song):
"""
    
    try:
        print("🤖 Sending prompt to AI...")
        response = model.generate_content(prompt)
        ai_text = response.text
        print(f"✅ AI Response: {ai_text}")
        return ai_text
    except Exception as e:
        print(f"⚠️ AI Rate Limited or Failed: {e}")
        
        # BETTER fallback with artist search handling
        if user_request['type'] == 'artist_search':
            artist_name = user_request['artist_name']
            if available_songs:
                import random
                random_song = random.choice(available_songs)
                return f"Love {artist_name}! 🎤 Here's a great track: {random_song}"
            else:
                return f"I'd love to find some {artist_name} tracks, but I couldn't find any in my database right now. Try searching directly on Spotify!"
        
        # Existing fallback logic for other types...
        if available_songs:
            # Find a song not in suggested_songs
            for song in available_songs:
                is_duplicate = False
                for suggested in suggested_songs:
                    if any(word in suggested.lower() for word in song.lower().split() if len(word) > 3):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    return f"Great taste in {user_request['genre_hint']}! 🎵 Try {song} 🎵"
            
            import random
            random_song = random.choice(available_songs)
            return f"Something fresh! 🎵 Try {random_song} 🎵"
        else:
            # 🎭 PERSONALITY FALLBACKS - More conversational
            if user_request['type'] == 'bengali':
                return "Bengali vibes incoming! 🇧🇩 Those soulful melodies hit different! Try 'Ei Raat Tomar Amar' by Kishore Kumar!"
            elif user_request['type'] == 'afrobeats':
                return "Afrobeats energy! 🌍 Time for some serious African rhythms! Try 'Ye' by Burna Boy!"
            elif user_request['type'] == 'tamil':
                return "Tamil vibes activated! 🇮🇳 Kollywood magic coming your way! Try 'Vaathi Coming' by Anirudh!"
            elif user_request['type'] == 'punjabi':
                return "Punjabi power! 🇮🇳 Get ready for some bhangra beats! Try 'Laembadgini' by Diljit Dosanjh!"
            elif user_request['type'] == 'hindi_bollywood':
                return "Bollywood vibes incoming! 🇮🇳 Those Hindi tracks just hit different! Try 'Jai Ho' by A.R. Rahman!"
            elif user_request['type'] == 'anime_japanese':
                return "Anime feels activated! 🇯🇵 Time for some epic J-music! Try 'Unravel' by TK from Ling tosite sigure!"
            elif user_request['type'] == 'kpop':
                return "K-pop energy detected! 🇰🇷 Ready for some serious vibes? Try 'Dynamite' by BTS!"
            else:
                return f"You've got excellent taste! 🎵 This one's gonna make your day! Try 'Happy' by Pharrell Williams!"

def extract_song_from_response(ai_text):
    """🔧 UPDATED: Extract song from conversational AI responses - Better for personality!"""
    print(f"🔍 Extracting song from: {ai_text}")
    
    # 🎭 UPDATED: Patterns optimized for conversational responses
    patterns = [
        # Try "Song" by Artist - main pattern (works with conversational text)
        r"[Tt]ry ['\"]([^'\"]+)['\"] by ([^.!?\n,🎵🎶🇯🇲🇧🇩🇮🇳🌍–—]+?)(?=[\s]*[.!?\n,🎵🎶🇯🇲🇧🇩🇮🇳🌍–—]|$)",
        
        # Check out "Song" by Artist  
        r"[Cc]heck out ['\"]([^'\"]+)['\"] by ([^.!?\n,🎵🎶🇯🇲🇧🇩🇮🇳🌍–—]+?)(?=[\s]*[.!?\n,🎵🎶🇯🇲🇧🇩🇮🇳🌍–—]|$)",
        
        # Listen to "Song" by Artist
        r"[Ll]isten to ['\"]([^'\"]+)['\"] by ([^.!?\n,🎵🎶🇯🇲🇧🇩🇮🇳🌍–—]+?)(?=[\s]*[.!?\n,🎵🎶🇯🇲🇧🇩🇮🇳🌍–—]|$)",
        
        # Go with "Song" by Artist
        r"[Gg]o with ['\"]([^'\"]+)['\"] by ([^.!?\n,🎵🎶🇯🇲🇧🇩🇮🇳🌍–—]+?)(?=[\s]*[.!?\n,🎵🎶🇯🇲🇧🇩🇮🇳🌍–—]|$)",
        
        # "Song" by Artist - standalone format (for when AI drops the intro)
        r"(?:^|[^a-zA-Z])['\"]([^'\"]+)['\"] by ([^.!?\n,🎵🎶🇯🇲🇧🇩🇮🇳🌍–—]+?)(?=[\s]*[.!?\n,🎵🎶🇯🇲🇧🇩🇮🇳🌍–—]|$)",
        
        # Try Song by Artist - without quotes (backup)
        r"[Tt]ry ([^🎵🎶\n–—]+?) by ([^🎵🎶\n.!?,–—🇯🇲🇧🇩🇮🇳🌍]+?)(?=[\s]*[.!?\n,🎵🎶🇯🇲🇧🇩🇮🇳🌍–—]|$)",
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, ai_text, re.IGNORECASE)
        if match:
            song_name = match.group(1).strip()
            artist_name = match.group(2).strip()
            
            # 🧹 ENHANCED CLEANUP: Remove more conversational trailing words and emojis
            cleanup_words = [
                r'\s*(–|—|\!|\?|\.|,)',  # Punctuation
                r'\s+it\'s',             # "it's"
                r'\s+that\'s',           # "that's" 
                r'\s+sweet',             # "sweet"
                r'\s+reggae',            # "reggae"
                r'\s+perfection',        # "perfection"
                r'\s+vibes',             # "vibes"
                r'\s+music',             # "music"
                r'\s+hits',              # "hits"
                r'\s+pure',              # "pure"
                r'\s+total',             # "total"
                r'\s+absolute',          # "absolute"
                r'\s+epic',              # "epic"
                r'\s+energy',            # "energy"
                r'\s+feels',             # "feels"
                r'\s+mood',              # "mood"
                r'\s+guaranteed',        # "guaranteed"
                r'\s+instant',           # "instant"
                r'\s+serious',           # "serious"
                r'\s+major',             # "major"
            ]
            
            # Apply all cleanup patterns
            for cleanup_pattern in cleanup_words:
                artist_name = re.sub(cleanup_pattern + r'.*$', '', artist_name, flags=re.IGNORECASE)
            
            artist_name = artist_name.strip().rstrip('!.?–—,-')
            
            # 🔧 ENHANCED: Better length handling for conversational responses
            if len(artist_name) > 35:
                words = artist_name.split()
                if len(words) > 3:
                    artist_name = ' '.join(words[:3])  # Take first 3 words for longer names
                elif len(words) > 1:
                    artist_name = ' '.join(words[:2])  # Take first 2 words otherwise
            
            # 🧹 FINAL CLEANUP: Remove any remaining problematic characters including regional flag emojis
            artist_name = re.sub(r'[🎵🎶🇯🇲🔥💯⚡🇧🇩🇮🇳🌍🇰🇷🇺🇸🇲🇽🇧🇷🇰🇪]', '', artist_name)  # Remove emojis
            artist_name = artist_name.strip()
            
            # Validate we have both song and artist
            if song_name and artist_name and len(artist_name) > 0:
                extracted = f"'{song_name}' by {artist_name}"
                print(f"✅ Extracted (pattern {i+1}): {extracted}")
                return extracted
            else:
                print(f"⚠️ Invalid extraction: song='{song_name}' artist='{artist_name}'")
    
    print("❌ No song extracted from AI response")
    return None

def generate_ai_response_personalized(user_message, user_request, available_songs, suggested_songs, user_data):
    """🎯 Generate PERSONALIZED AI response using user's actual Spotify data"""
    
    # 🔧 FIX 4: Use correct data structure key
    preferences = user_data.get('preferences', {})  # ✅ Fixed: was 'music_preferences'
    profile = user_data.get('profile', {})
    
    # Validate we have preferences
    if not preferences:
        print(f"❌ No preferences found in user_data: {user_data.keys()}")
        print(f"🔄 Falling back to general AI response")
        return generate_ai_response(user_message, user_request, available_songs, suggested_songs)
    
    top_genres = preferences.get('top_genres', [])[:3]
    favorite_artists = preferences.get('favorite_artists', [])[:3]
    display_name = profile.get('display_name', 'music lover')
    
    print(f"🎯 PERSONALIZED AI: User {display_name}")
    print(f"🎵 Top genres: {top_genres}")
    print(f"🎤 Favorite artists: {favorite_artists}")
    
    # Create the song list for AI prompt
    if available_songs:
        songs_list = "\n".join([f"- {song}" for song in available_songs[:20]])
    else:
        songs_list = "No matching songs found in database"
    
    # 🧠 MEMORY: Create exclusion list for AI
    exclusion_text = ""
    if suggested_songs:
        exclusion_text = f"""

🚨🚨🚨 CRITICAL MEMORY RULE - ABSOLUTELY NEVER suggest these songs (already suggested):
{chr(10).join([f"❌ {song}" for song in suggested_songs])}

⚠️ IF YOU SUGGEST ANY OF THE ABOVE SONGS, THE SYSTEM WILL BREAK!
✅ YOU MUST suggest a COMPLETELY DIFFERENT song from the available list above!
🔄 Memory check: {len(suggested_songs)} songs already suggested - pick something NEW!"""

    # 🎯 ENHANCED PERSONALIZED PROMPT
    prompt = f"""
You are YAIN, a cheeky, witty music chatbot with personality! You know {display_name}'s music taste from their Spotify account.

User said: "{user_message}"

🎵 {display_name.upper()}'S ACTUAL MUSIC TASTE (from Spotify):
- Favorite genres: {', '.join(top_genres) if top_genres else 'Still analyzing...'}
- Favorite artists: {', '.join(favorite_artists) if favorite_artists else 'Still analyzing...'}

Your response should:
1. **IMMEDIATELY acknowledge their personal taste** ("Hey {display_name}! I see you love {top_genres[0] if top_genres else 'great music'}!")
2. Be excited that you know their personal taste
3. Connect their request to their actual music preferences when relevant
4. Then suggest that specific song with "Try 'Song Name' by Artist Name"

WHAT THEY WANT: {user_request['genre_hint']}

AVAILABLE SONGS FOR THIS REQUEST:
{songs_list}
{exclusion_text}

INSTRUCTIONS:
- Start with their NAME and mention their ACTUAL Spotify taste immediately
- Be personalized and excited about knowing their preferences
- Pick ONE song from the available list above
- Format as: "Try 'Song Name' by Artist Name"
- ⚠️ NEVER EVER repeat songs from the exclusion list above
- 🧠 MEMORY: You have suggested {len(suggested_songs)} songs before - pick something COMPLETELY different!

Examples of GOOD personalized responses:
"Hey {display_name}! I know you're into {top_genres[0] if top_genres else 'indie rock'} and love {favorite_artists[0] if favorite_artists else 'Taylor Swift'} - this mood is perfect for your taste! Try..."
"Oh {display_name}! Your Spotify shows you're big on {top_genres[0] if top_genres else 'alternative'} - I've got the PERFECT match! Try..."

⚠️ CRITICAL: Your response MUST acknowledge their personal music taste in the first sentence!

Your personalized response:
"""
    
    try:
        print("🤖 Sending PERSONALIZED prompt to AI...")
        response = model.generate_content(prompt)
        ai_text = response.text
        print(f"✅ PERSONALIZED AI Response: {ai_text}")
        return ai_text
    except Exception as e:
        print(f"⚠️ Personalized AI failed, using fallback: {e}")
        # Create a quick personalized fallback
        if top_genres and favorite_artists:
            if available_songs:
                import random
                song = random.choice(available_songs)
                return f"Hey {display_name}! I see you love {top_genres[0]} and {favorite_artists[0]} - perfect taste! Try {song}"
            else:
                return f"Hey {display_name}! Your taste in {top_genres[0]} is *chef's kiss*! Let me find something perfect for you..."
        else:
            # Fallback to regular AI response
            return generate_ai_response(user_message, user_request, available_songs, suggested_songs)