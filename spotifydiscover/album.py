from spotifydiscover.source import Source


class Album(Source):
    def __init__(self, resource, quick):
        super().__init__(resource, quick)
        self.priority = 1

    def calculate_priority(self, average_share, average_exploitation, share_bonus_modifier):
        # TODO: Add priority rules such as similarity in release time and features to exploited records.
        """
        Calculates album priority based on source shares, exploitation and discovery configuration.

        Priority is calculated by the following steps:
        - Any share of source increases priority, how much depends on average album shares in the source collection.
        - Exploitation of the album as compared to the average further modifies the priority.
        - Additional discovery rules can influence the album priority.
        """
        # TODO: Check is the exploitation multiplier doesn't get too crazy
        # Alternative
        # extra_priority = share_bonus_modifier * (self.source_share/average_share) * (self.exploitation/average_exploitation)
        extra_priority = ((share_bonus_modifier * (self.source_share / average_share)) + (
                share_bonus_modifier * (self.exploitation / average_exploitation))) / 2
        self.priority = 1 + extra_priority

    def load_tracks(self):
        """Load all tracks calculate collection length."""
        # TODO: Albums only load tracks to precisely calculate length, which is pretty overkill even with quick mode off, make it a separate option
        if self.quick:
            # In quick mode estimate number of tracks from metadata.
            self.total_tracks = self.resource.count_tracks()
        else:
            self.total_tracks = len(self.resource.get_tracks())

