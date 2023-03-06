import time
import spotifytools.spotify as spotify
import spotifytools.helpers as helpers
from spotifytools.spotify_session import SpotifySession


class Source:
    """
    Wrapper for any actor object in the discovery algorithm, like artist or album.

    Valid types of resource are classes that inherit both spotify.Resource and spotify.Collection.
    """

    def __init__(self, resource: spotify.Collection, quick, print=False):
        # `quick` means the artist will have less than 10 tracks and it's not needed to load everything.
        # TODO: In the future this will probably be replaced by an entire dictionary of rules and variables.
        self.quick = quick
        self.resource = resource
        self.source_tracks = []  # All tracks from this source present in the source collection.
        self.total_tracks = None  # In quick mode is summed up from albums' 'total_tracks' attribute.
        self.undiscovered_tracks = None  # Unique tracks that aren't in the source collection.
        self.exploitation = None  # Fraction of this resource's material already present in the source collection.
        self.source_share = None  # Fraction of the original collection contributed by this resource.
        # Copy over the resource's attributes to skip unnecessary calls to resource.
        self.__dict__.update(self.resource.__dict__)

    def __eq__(self, other):
        """Allow comparing to uri strings and resource objects to simplify code."""
        match other:
            case str():
                return other == self.uri
            case spotify.Artist() | spotify.Album():
                return self.resource == other
            case _:
                return other is self

    def calculate_exploitation(self):
        """Calculates how much of artist's total original material is already present in the source collection."""
        # Some artists may not have anything considered as tracks, for example when they only release singles.
        if self.total_tracks == 0:
            self.exploitation = 0
        else:
            self.exploitation = len(self.source_tracks) / self.total_tracks
        # Uniqueness must be decided by the same rules, so the exploitation quotient must be between 0 and 1.
        if self.exploitation > 1 or self.exploitation < 0:
            # TODO: This is unreliable
            self.exploitation = 0

            #raise Exception(f"Discovery exploitation quotient is not a valid fraction: {self.exploitation}.")
        return self.exploitation

    def calculate_source_share(self, source_length):
        self.source_share = len(self.source_tracks) / source_length
        return self.source_share

