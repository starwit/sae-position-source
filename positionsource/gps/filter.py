import math
from typing import NamedTuple
from datetime import datetime
from .util import ll_to_xy, xy_to_ll


class GPSFilterState(NamedTuple):
    timestamp: datetime
    lat: float
    lon: float
    speed_kmh: float
    heading_deg: float


class GPSFilter:
    '''
    An implementation of an alpha-beta filter for GPS position smoothing with additional spike rejection.
    See: https://en.wikipedia.org/wiki/Alpha_beta_filter
    '''
    def __init__(
        self,
        alpha=0.75,
        beta=0.05,
        spike_radius_m=80.0,
    ):
        self.alpha = alpha
        self.beta = beta

        self.spike_radius_m = spike_radius_m

        self._init_params()

    def _init_params(self):
        self.origin_lat = None
        self.origin_lon = None

        self.x = None
        self.y = None
        self.vx = 0.0
        self.vy = 0.0

        self.last_t = None
        self.stop_timer = 0.0

    def reset(self):
        self._init_params()

    def update(self, lat: float, lon: float, timestamp_ms: float) -> GPSFilterState:
        """
        lat/lon in decimal degrees
        timestamp_ms = timestamp in milliseconds
        """

        t = timestamp_ms / 1000.0

        # first point initializes system
        if self.origin_lat is None:
            self.origin_lat = lat
            self.origin_lon = lon

            self.x = 0.0
            self.y = 0.0
            self.last_t = t

            return GPSFilterState(timestamp=datetime.fromtimestamp(t), lat=lat, lon=lon, speed_kmh=0.0, heading_deg=0.0)

        # convert measurement to local coordinates
        x_meas, y_meas = ll_to_xy(lat, lon, self.origin_lat, self.origin_lon)

        dt = t - self.last_t
        if dt <= 0:
            dt = 1e-3

        # ----------------------------
        # Predict
        # ----------------------------
        x_pred = self.x + self.vx * dt
        y_pred = self.y + self.vy * dt

        # residual
        rx = x_meas - x_pred
        ry = y_meas - y_pred

        residual_dist = math.hypot(rx, ry)

        # ----------------------------
        # Spike rejection
        # ----------------------------
        if residual_dist > self.spike_radius_m:
            # ignore impossible jump
            rx = 0.0
            ry = 0.0

        # ----------------------------
        # Correct location and velocity
        # ----------------------------
        self.x = x_pred + self.alpha * rx
        self.y = y_pred + self.alpha * ry

        self.vx = self.vx + self.beta * rx / dt
        self.vy = self.vy + self.beta * ry / dt

        self.last_t = t

        # ----------------------------
        # Derived values
        # ----------------------------
        speed = math.hypot(self.vx, self.vy)

        heading = math.degrees(math.atan2(self.vx, self.vy))
        heading = (heading + 360) % 360

        out_lat, out_lon = xy_to_ll(self.x, self.y, self.origin_lat, self.origin_lon)

        return GPSFilterState(
            timestamp=datetime.fromtimestamp(self.last_t),
            lat=out_lat,
            lon=out_lon,
            speed_kmh=speed * 3.6,
            heading_deg=heading,
        )