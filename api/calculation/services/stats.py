from calculation.models import Parameters, Track, UnitPrice
from django.db.models import Subquery, OuterRef, Sum, F, Q
from datetime import timedelta
from decimal import Decimal

from calculation.models import Plate


class Stats:

    @staticmethod
    def calculate_concrete_economy_kpi(tracks):
        """
        Calculates KPI for concrete economy.

        For each track, finds the maximum concrete class and calculates the penalty
        as the sum of (max_class - plate_class) * plate_length for all plates on the track.

        Lower value is better.
        """
        plate_class_prices = UnitPrice.get_plates_prices()
        total_penalty = 0

        for track in tracks:
            plates = list(track.plates.all())
            if not plates:
                continue

            # Get concrete classes used on this track
            concrete_classes = [plate.concrete_class for plate in plates]
            if not concrete_classes:
                continue

            # Find the maximum concrete class by price
            max_class = max(concrete_classes, key=lambda c: plate_class_prices.get(c, 0))
            max_price = plate_class_prices.get(max_class, 0)

            # Calculate penalty for each plate
            for plate in plates:
                plate_price = plate_class_prices.get(plate.concrete_class, 0)
                if max_price > plate_price:
                    # Penalty is proportional to the price difference and plate length
                    # Convert plate.length to Decimal to avoid type mismatch
                    penalty = (max_price - plate_price) * (Decimal(str(plate.length)) / 1000)
                    total_penalty += penalty
        total_penalty /= len(tracks)
        return total_penalty

    @staticmethod
    def calculate_wire_economy_kpi(tracks):
        """
        Calculates KPI for wire economy.

        For each track, finds the maximum wire counts (top and bottom) and calculates the penalty
        as the sum of (max_wire - plate_wire) * plate_length for all plates on the track.

        Lower value is better.
        """
        total_penalty = 0

        for track in tracks:
            plates = list(track.plates.all())
            if not plates:
                continue

            # Get maximum wire counts on this track
            max_wire_top = max([int(plate.wire_top) for plate in plates], default=0)
            max_wire_bottom = max([int(plate.wire_bottom) for plate in plates], default=0)

            # Calculate penalty for each plate
            for plate in plates:
                wire_top_diff = max_wire_top - int(plate.wire_top)
                wire_bottom_diff = max_wire_bottom - int(plate.wire_bottom)

                # Penalty is proportional to the wire difference and plate length
                # Convert plate.length to Decimal to avoid type mismatch
                penalty = (wire_top_diff + wire_bottom_diff) * (Decimal(str(plate.length)) / 1000)
                total_penalty += penalty
        total_penalty /= len(tracks)
        return total_penalty

    @staticmethod
    def calculate_deadline_kpi(tracks):
        """
        Calculates KPI for meeting deadlines.

        For each plate, checks if it's overdue and calculates the penalty
        as the square of the number of days overdue.

        Lower value is better.
        """
        total_penalty = 0
        parameters = Parameters.get_solo()
        production_lag = parameters.production_lag or 0

        for track in tracks:
            plates = list(track.plates.all())
            for plate in plates:
                if not plate.deadline or not plate.deadline.date:
                    continue

                # Calculate days overdue
                deadline_date = plate.deadline.date - timedelta(days=production_lag)
                if track.day > deadline_date:
                    days_overdue = (track.day - deadline_date).days
                    # Penalty is the square of days overdue
                    penalty = days_overdue ** 2
                    total_penalty += penalty
        total_penalty /= len(tracks)
        return total_penalty

    @staticmethod
    def calculate_track_loading_kpi(tracks):
        """
        Calculates KPI for track loading.

        Calculates the percentage of track length utilized and returns
        the penalty as 100 - utilization_percentage.

        Lower value is better.
        """
        road_length = Parameters.get_solo().road_length
        total_available_length = len(tracks) * road_length
        total_used_length = sum(track.useful_length for track in tracks)

        if total_available_length == 0:
            return 100  # Maximum penalty if no tracks available

        utilization_percentage = (total_used_length / total_available_length) * 100
        penalty = 100 - utilization_percentage

        return penalty

    @staticmethod
    def calculate_retooling_kpi(tracks):
        """
        Calculates KPI for equipment retooling.

        Counts the number of configuration changes (width x height) per day
        and returns the average number of changes per track.

        Lower value is better.
        """
        total_retoolings = 0
        days = set(track.day for track in tracks)

        for day in days:
            day_tracks = [t for t in tracks if t.day == day]
            configurations = set()

            for track in day_tracks:
                if track.width and track.height:
                    configurations.add((track.width, track.height))

            # Number of reconfigurations is the number of unique configurations minus 1
            # (if there's only one configuration, no reconfiguration is needed)
            day_retoolings = len(configurations) - 1 if configurations else 0
            total_retoolings += max(0, day_retoolings)

        # Average retoolings per track
        avg_retoolings = total_retoolings / len(tracks) if tracks else 0

        return avg_retoolings

    @staticmethod
    def calculate_efficiency_score(tracks, weights=None):
        """
        Calculates the overall efficiency score based on the 5 KPI metrics.

        E = α·Eбетон + β·Eпроволока + γ·Eдедлайны + δ·Eзагрузка + ε·Eпереналадки

        Lower value is better.
        """
        # Default weights if not provided
        if weights is None:
            weights = {
                'concrete': 1.0,
                'wire': 1.0,
                'deadline': 1.0,
                'loading': 1.0,
                'retooling': 1.0
            }

        # Calculate individual KPIs
        concrete_kpi = Stats.calculate_concrete_economy_kpi(tracks)
        wire_kpi = Stats.calculate_wire_economy_kpi(tracks)
        deadline_kpi = Stats.calculate_deadline_kpi(tracks)
        loading_kpi = Stats.calculate_track_loading_kpi(tracks)
        retooling_kpi = Stats.calculate_retooling_kpi(tracks)

        # Calculate weighted sum
        # Convert all KPI values to Decimal to avoid type mismatch
        efficiency_score = (
            Decimal(str(weights['concrete'])) * Decimal(str(concrete_kpi)) +
            Decimal(str(weights['wire'])) * Decimal(str(wire_kpi)) +
            Decimal(str(weights['deadline'])) * Decimal(str(deadline_kpi)) +
            Decimal(str(weights['loading'])) * Decimal(str(loading_kpi)) +
            Decimal(str(weights['retooling'])) * Decimal(str(retooling_kpi))
        )

        # Return both the overall score and individual components
        return {
            'score': efficiency_score,
            'concrete_economy': concrete_kpi,
            'wire_economy': wire_kpi,
            'deadline_compliance': deadline_kpi,
            'track_loading': loading_kpi,
            'retooling_efficiency': retooling_kpi
        }

    @staticmethod
    def get_all_stats():

        all_tracks = Track.objects.all()

        all_max_length = (all_tracks.count() * Parameters.get_solo().road_length)

        retool_count = 0
        for day in set(Track.objects.all().values_list('day', flat=True)):
            day_tracks = Track.objects.filter(day=day)
            day_retool_count = len(set((t.width, t.height) for t in day_tracks if t.width and t.height))
            if day_retool_count > 0:
                day_retool_count -= 1
            retool_count += day_retool_count

        retool_price = retool_count * UnitPrice.get_retooling_price()
        all_cost = sum([track.cost for track in all_tracks])
        useful = (sum([track.useful_length for track in all_tracks]) / all_max_length if all_max_length else 0)
        track_id_subquery = Subquery(Plate.objects.filter(track_id=OuterRef('id')).values('track_id').distinct().values('track_id'))
        last_track = Track.objects.filter(id__in=track_id_subquery).order_by('-day').first()

        # Calculate KPI efficiency score
        kpi_data = Stats.calculate_efficiency_score(Track.get_current_week_tracks())

        return {
            'tracks': sum([int(track.plates.exists()) for track in all_tracks]),
            'plates': sum([track.plates.count() for track in all_tracks]),
            'useful': round(useful * 100, 2),
            'retool_count': retool_count,
            'retool_price': retool_price,
            'all_cost': all_cost,
            'last_track': last_track.day if last_track else 'Нет данных',
            'kpi_score': round(kpi_data['score'], 2),
            'kpi_concrete_economy': round(kpi_data['concrete_economy'], 2),
            'kpi_wire_economy': round(kpi_data['wire_economy'], 2),
            'kpi_deadline_compliance': round(kpi_data['deadline_compliance'], 2),
            'kpi_track_loading': round(kpi_data['track_loading'], 2),
            'kpi_retooling_efficiency': round(kpi_data['retooling_efficiency'], 2)
        }

    @staticmethod
    def get_today_stats():
        today_tracks = Track.get_today_tracks()

        today_max_length = (len(today_tracks) * Parameters.get_solo().road_length)
        today_useful = sum([track.useful_length for track in today_tracks]) / today_max_length if today_max_length else 0

        # Calculate KPI efficiency score for today
        kpi_data = Stats.calculate_efficiency_score(today_tracks)

        return {
            'tracks': sum([int(track.plates.exists()) for track in today_tracks]),
            'plates': sum([track.plates.count() for track in today_tracks]),
            'useful': round(today_useful * 100, 2),
            'kpi_score': round(kpi_data['score'], 2),
            'kpi_concrete_economy': round(kpi_data['concrete_economy'], 2),
            'kpi_wire_economy': round(kpi_data['wire_economy'], 2),
            'kpi_deadline_compliance': round(kpi_data['deadline_compliance'], 2),
            'kpi_track_loading': round(kpi_data['track_loading'], 2),
            'kpi_retooling_efficiency': round(kpi_data['retooling_efficiency'], 2)
        }
