# ------------------------------------------------------------
# © 2025 Samia Islam. All rights reserved.
# This file is part of the "YAIN" project.
# Released under CC BY-NC 4.0 license.
# For demo and educational use only — not for commercial use.
# ------------------------------------------------------------




# Services package for YAIN
# Organized modules for clean code structure


from .spotify_service import (
    get_trending_songs,
    search_spotify_song, 
    search_specific_genre,
    search_artist_songs,
    spotify,  # Export spotify client for dynamic artist detection
    SPOTIFY_ENABLED
)
from .ai_service import (
    analyze_user_request,
    generate_ai_response,
    extract_song_from_response
)

from .memory_service import (
    filter_trending_songs,
    create_memory_stats,
    validate_memory_system
)

from .youtube_service import (
    search_youtube_song,
    YOUTUBE_ENABLED
)

# DISABLED FOR NOW - Uncomment when ready to deploy with auth
# from .user_service import (
#     spotify_auth,
#     create_user_profile,
#     UserPreferenceManager
# )