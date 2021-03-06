#!/usr/bin/env python
from numpy import atleast_1d, empty_like, pi, nan
from datetime import datetime
from astropy.time import Time
import astropy.units as u
from astropy.coordinates import Longitude
"""
input longitude and output are in RADIANS!

Note: The "usevallado" datetime to julian runs 4 times faster than astropy.
AstroPy is more accurate, but version 1.0.0 doesn't auto-download new IERS data
for current/future times, giving an
IndexError: (some) times are outside of range covered by IERS table.
"""


def datetime2sidereal(t, lon_radians, usevallado=True):
    t = atleast_1d(t)
    assert isinstance(t[0], datetime)
    # lon: longitude in RADIANS

    if usevallado:
        jd = datetime2julian(t)
        gst = julian2sidereal(jd)  # Greenwich Sidereal time RADIANS
        return gst + lon_radians  # radians # Algorithm 15 p. 188 rotate to LOCAL SIDEREAL TIME
    else:  # astropy
        try:
            return Time(t).sidereal_time(kind='apparent',
                                         longitude=Longitude(lon_radians, unit=u.radian)).radian
        except IndexError as e:
            print('possible IERS table Astropy issue, falling back to Vallado  {}'.format(e))
            return datetime2sidereal(t, lon_radians, True)


def datetime2julian(dtm):
    """
    from D.Vallado Fundamentals of Astrodynamics and Applications p.187
     and J. Meeus Astronomical Algorithms 1991 Eqn. 7.1 pg. 61
    """
    dtm = atleast_1d(dtm)

    jDate = empty_like(dtm, dtype=float)  # yes we need the dtype!

    for i, d in enumerate(dtm):
        if d is None:
            jDate[i] = nan
            continue

        if d.month < 3:
            year = d.year - 1
            month = d.month + 12
        else:
            year = d.year
            month = d.month

        A = int(year / 100.0)
        B = 2 - A + int(A / 4.)
        C = ((d.second / 60. + d.minute) / 60. + d.hour) / 24.
        jDate[i] = int(365.25 * (year + 4716)) + \
            int(30.6001 * (month + 1)) + d.day + B - 1524.5 + C

    return jDate


def julian2sidereal(juliandate):
    # D. Vallado Ed. 4
    # TODO needs unit testing
    # Julian centuries from J2000.0
    tUT1 = (juliandate - 2451545.0) / \
        36525.  # Vallado Eq. 3-42 p. 184, Seidelmann 3.311-1

    gmst_sec = 67310.54841 + (876600 * 3600 + 8640184.812866) * \
        tUT1 + 0.093104 * tUT1**2 - 6.2e-6 * tUT1**3  # Eqn. 3-47 p. 188

    # 1/86400 and %(2*pi) implied by units of radians
    return gmst_sec * (2 * pi) / 86400. % (2 * pi)

if __name__ == '__main__':
    from dateutil.parser import parse
    from argparse import ArgumentParser
    p = ArgumentParser(
        description="convert datetime to sidereal time (astropy converts datetime to julian")
    p.add_argument('time', help='time of observation YYYY-mm-ddTHH:MM:SS')
    p.add_argument('lon_radians', help='obs location in radians', type=float)
    a = p.parse_args()

    try:
        sidereal = datetime2sidereal(parse(a.time),  a.lon_radians)
        print(sidereal)
    except TypeError:
        raise TypeError('input a datetime  YYYY-dd-mmTHH:MM:SS and longitude in RADIANS')
