import os
from dotenv import load_dotenv
load_dotenv()
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Tuple, Dict
import openai

serperdev_api_key = os.getenv("SERPERDEV_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
spotipy_client_id = os.getenv("SPOTIPY_CLIENT_ID")
spotipy_client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

openai.api_key = openai_api_key

spotify = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=spotipy_client_id,
        client_secret=spotipy_client_secret
    )
)

def fetch_playlist_data(query: str) -> Dict:
    headers = {
        'Authorization': f'Bearer {serperdev_api_key}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(
            f'https://google.serper.dev/search?q=&apiKey=3985e8024153834462bacff357bacea200546eff',
            params={'q': query},
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Serper: {e}")
        return {'organic': []}

def recommend_similar_songs(song_title: str) -> List[str]:
    try:
        # Search for the track
        search_results = spotify.search(q=song_title, type='track', limit=1)
        tracks = search_results['tracks']['items']
        
        if not tracks:
            return ["No similar songs found."]

        track_id = tracks[0]['id']
        
        # Get recommendations
        x=int(input('How many songs do you want: '))
        recommendations = spotify.recommendations(seed_tracks=[track_id], limit=x)
        similar_songs = [f"{track['name']} by {track['artists'][0]['name']}" 
                        for track in recommendations['tracks']]
        
        return similar_songs
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return ["Error fetching recommendations."]

def generate_playlist_description(songs: List[str]) -> str:
    """
    Generate a playlist description
    
    Args:
        songs (List[str]): List of song titles
    
    Returns:
        str: Generated playlist description
    """
    try:
        prompt = f"Create a short playlist description based on these songs: {', '.join(songs)}"
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        #print(f"Error generating playlist description: {e}"
        return "Custom playlist"

def create_playlist(query: str) -> Tuple[str, List[str]]:
    """
    Generate a playlist using the search query.
    
    Args:
        query (str): User's playlist query
    
    Returns:
        Tuple[str, List[str]]: Playlist description and list of relevant songs
    """
    # Fetch search results
    search_results = fetch_playlist_data(query)
    
    # Extract relevant song titles from search results
    relevant_songs = []
    for result in search_results.get('organic', []):
        if 'title' in result:
            relevant_songs.append(result['title'])
    
    if not relevant_songs:
        return "No songs found.", []
    # Generate playlist description
    playlist_description = generate_playlist_description(relevant_songs[:5])
    
    return playlist_description, relevant_songs

def create_spotify_playlist(self, name: str, description: str, track_ids: List[str]):
        """Create a Spotify playlist with the given tracks."""
        try:
            user_id = self.spotify_auth.me()['id']
            playlist = self.spotify_auth.user_playlist_create(
                user_id,
                name,
                public=True,
                description=description
            )
            
            if track_ids:
                self.spotify_auth.playlist_add_items(playlist['id'], track_ids)
            
            return playlist['external_urls']['spotify']
        except Exception as e:
            print(f"Error creating playlist: {e}")
            return None

def main():
    """Main function to run the playlist generator."""
    try:
        user_query = input("What type of playlist do you want? ")
        playlist_description, relevant_songs = create_playlist(user_query)
        
#        print("\nGenerated Playlist Description:")
#        print(playlist_description)

        if relevant_songs:
            similar_songs = recommend_similar_songs(relevant_songs[0])
            print("Here's your playlist. Enjoy!")
            for i, song in enumerate(similar_songs, 1):
                print(f"{i}. {song}")
        '''print("Here's the link for the spotify playlist.")
        create_spotify_playlist()
        print(playlist)'''
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()