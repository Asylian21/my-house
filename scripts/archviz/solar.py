"""NOAA solar approximation; UTC-aware datetime, azimuth clockwise from north."""

import math
from datetime import datetime, timezone


def solar_position(iso_datetime, latitude, longitude):
    instant = datetime.fromisoformat(iso_datetime)
    if instant.tzinfo is None:
        raise ValueError(
            "Solar date must include UTC offset, e.g. 2026-09-04T17:00:00+02:00"
        )
    utc = instant.astimezone(timezone.utc)
    days = (utc - datetime(2000, 1, 1, 12, tzinfo=timezone.utc)).total_seconds() / 86400
    t = days / 36525
    mean_long = (280.46646 + t * (36000.76983 + 0.0003032 * t)) % 360
    anomaly = math.radians((357.52911 + t * (35999.05029 - 0.0001537 * t)) % 360)
    eccentricity = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    center = (
        (1.914602 - t * (0.004817 + 0.000014 * t)) * math.sin(anomaly)
        + (0.019993 - 0.000101 * t) * math.sin(2 * anomaly)
        + 0.000289 * math.sin(3 * anomaly)
    )
    omega = math.radians(125.04 - 1934.136 * t)
    apparent = math.radians(mean_long + center - 0.00569 - 0.00478 * math.sin(omega))
    obliquity = math.radians(
        23
        + (26 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60) / 60
        + 0.00256 * math.cos(omega)
    )
    declination = math.asin(math.sin(obliquity) * math.sin(apparent))
    y = math.tan(obliquity / 2) ** 2
    l = math.radians(mean_long)
    eq = 4 * math.degrees(
        y * math.sin(2 * l)
        - 2 * eccentricity * math.sin(anomaly)
        + 4 * eccentricity * y * math.sin(anomaly) * math.cos(2 * l)
        - 0.5 * y * y * math.sin(4 * l)
        - 1.25 * eccentricity**2 * math.sin(2 * anomaly)
    )
    minutes = utc.hour * 60 + utc.minute + utc.second / 60
    ha = math.radians(((minutes + eq + 4 * longitude) % 1440) / 4 - 180)
    lat = math.radians(latitude)
    elevation = math.asin(
        math.sin(lat) * math.sin(declination)
        + math.cos(lat) * math.cos(declination) * math.cos(ha)
    )
    azimuth = (
        math.atan2(
            math.sin(ha),
            math.cos(ha) * math.sin(lat) - math.tan(declination) * math.cos(lat),
        )
        + math.pi
    ) % (2 * math.pi)
    return elevation, azimuth


def site_sun_direction(elevation, azimuth, north_angle):
    a = azimuth + north_angle
    return (
        math.sin(a) * math.cos(elevation),
        math.cos(a) * math.cos(elevation),
        math.sin(elevation),
    )
