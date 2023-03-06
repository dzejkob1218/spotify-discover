import time
import spotifytools.spotify as spotify
import spotifytools.helpers as helpers
from spotifytools.spotify_session import SpotifySession
from spotifydiscover.source import Source
from typing import List

class Artist(Source):
    def __init__(self, resource, quick):
        super().__init__(resource, quick)
        self.result_total = 0  # Tracks this artist will contribute to the resulting collection.
        self.top10 = False
        self.contribution = 0
        self.spillover = None
        self.related_artists: List[Artist] = []
        self.share_contributors = []  # Artists who passed their shares onto this artist due to relation

    def estimate_total_tracks(self):
        """Estimate the number of tracks in this resource without loading them."""
        self.total_tracks = self.resource.count_tracks()

    def load_top_tracks(self):
        """Load top 10 tracks."""
        # TODO: This would introduce a redundant request if the 10 isn't enough
        unique_top_tracks = self.resource.get_top_tracks(remove_duplicates=True)
        undiscovered_top_tracks = helpers.remove_duplicates(unique_top_tracks, self.source_tracks)

        # Use top tracks as source if it's sufficient
        if len(undiscovered_top_tracks) >= self.result_total:
            self.top10 = True
            self.undiscovered_tracks = undiscovered_top_tracks
            return self.undiscovered_tracks
        else:
            self.quick = False

    def load_undiscovered_tracks(self):
        """Load all undiscovered tracks."""
        # If quick mode was off or more tracks are contributed than are available in top tracks, load everything.
        # This is the bit that takes the most time, but there is no way around it.
        # TODO: Some ways to decrease time would be to not load popularity and keep a random order or prioritise using albums that are already present in the collection
        all_tracks = self.resource.get_tracks()

        # TODO: The removal of duplicates functionality here has been lost
        unique_tracks = self.resource.sp.load_details(all_tracks)
        # Remember the original length to calculate exploitation.
        self.total_tracks = len(unique_tracks)

        self.undiscovered_tracks = helpers.remove_duplicates(unique_tracks, self.source_tracks)

        return self.undiscovered_tracks

    def set_discovery_priority(self, albums):
        """
        Arrange undiscovered tracks in discovery priority.

        The order is decided by track sorting rules and album priority.
        By default tracks are sorted by popularity and albums gain priority only by their shares and exploitation.
        """

        # TODO: Expand this method to accept custom track and album sorting rules.
        def album_priority(track):
            return next((album.priority for album in albums if track.album == album), 1)

        def track_priority(track):
            return track.popularity

        sorting_key = lambda track: track_priority(track) * album_priority(track)
        self.undiscovered_tracks = sorted(self.undiscovered_tracks, key=sorting_key, reverse=True)

    def estimate_result_share(self, result_size):
        """
        Approximates the share of the result for this artist.

        This is significant in quick mode, and is used to check if the artist should be limited to top 10 tracks.
        """
        self.result_total = round(self.source_share * result_size)
        return self.result_total

    def calculate_result_total(self, result_size, average_exploitation, exploitation_bonus_modifier):
        """
        Calculates how many songs the artist will contribute to the resulting collection.
        """
        # TODO: Experiment to find the best point to round the shares
        exploitation_quotient = (self.exploitation / average_exploitation)  # * exploitation_bonus_modifier
        exploitation_bonus = (exploitation_quotient - 1) * exploitation_bonus_modifier
        self.result_total = int(round(self.source_share * result_size * (1 + exploitation_bonus)))
        return self.result_total

    def calculate_result_exploitation(self):
        """Calculate how much of the artist's material would be used in the result."""
        e = (self.result_total + len(self.source_tracks))/self.total_tracks if self.total_tracks else 0
        if e > 1:
            e =1
        return e

    def calculate_spillover(self, spillover_parameter):
        spillover = 0

        exp = self.calculate_result_exploitation()
        spillover_rate = exp * spillover_parameter

        self.spillover = min(int(spillover + round(spillover_rate * self.result_total)), self.result_total)
        self.contribution = self.result_total - self.spillover

        # TODO: This will prevent artists using top 10 to load all their tracks when needed
        if self.contribution > len(self.undiscovered_tracks):
            self.spillover += self.contribution - len(self.undiscovered_tracks)
            self.contribution = len(self.undiscovered_tracks)

        return self.spillover

    def load_related_artists(self):
        """
        Load and sort related artists.

        Sorting rules:
        - Newly created artists are put first
        - Existing artists not present in source collection are second
        - Artists present in the source collection are last
        - Artists with bigger shares than this one are removed
        """
        related_total = len(self.related_artists)
        # TODO : Some artists don't have relates
        if not related_total:
            return
        share = self.spillover // related_total
        for i in range(min(related_total, self.spillover)):
            relate = self.related_artists[i]
            # TODO: Let new artists load all tracks
            if not relate.undiscovered_tracks:
                relate.load_top_tracks()
            relate.contribution += share + (1 if i <= self.spillover % related_total else 0)
            relate.share_contributors.append(self)
