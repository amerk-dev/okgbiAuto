from calculation.models import Parameters, Track, UnitPrice



class Stats:

    @staticmethod
    def get_all_stats():

        all_tracks = Track.objects.all()

        all_max_length = (all_tracks.count() * Parameters.get_solo().road_length)

        retool_count = sum([len(track.retoolings) for track in all_tracks])
        retool_price = retool_count * UnitPrice.get_retooling_price()
        all_cost = sum([track.cost for track in all_tracks])
        useful = (sum([track.useful_length for track in all_tracks]) / all_max_length if all_max_length else 0)
        return {
            'tracks': sum([int(track.plates.exists()) for track in all_tracks]),
            'plates': sum([track.plates.count() for track in all_tracks]),
            'useful': round(useful * 100, 2),
            'retool_count': retool_count,
            'retool_price': retool_price,
            'all_cost': all_cost
        }

    @staticmethod
    def get_today_stats():
        today_tracks = Track.get_today_tracks()

        today_max_length = (len(today_tracks) * Parameters.get_solo().road_length)
        today_useful = sum([track.useful_length for track in today_tracks]) / today_max_length if today_max_length else 0
        return {
            'tracks': sum([int(track.plates.exists()) for track in today_tracks]),
            'plates': sum([track.plates.count() for track in today_tracks]),
            'useful': round(today_useful * 100, 2),
        }