"""
Michael Hirsch ported and adaptation from
 GNU Octave Mapping Toolbox by
  Copyright (c) 2013, Sandeep V. Mahanthi
Copyright (c) 2013, Felipe G. Nievinski

Input/output: units are METERS and DEGREES.
boolean deg=True means degrees

For most functions you can input Numpy arrays of any shape,
except as noted in the functions

see test.py for example uses.
"""
from __future__ import division
from numpy import (sin, cos, tan, sqrt, radians, arctan2, hypot, degrees, mod,
                   atleast_2d, atleast_1d, empty_like, array, column_stack)
from astropy.time import Time
from datetime import datetime


class EarthEllipsoid:

    def __init__(self):
        self.a = 6378137.  # semi-major axis [m]
        self.f = 1 / 298.2572235630  # flattening
        self.b = self.a * (1 - self.f)  # semi-minor axis


def aer2ecef(az, el, srange, lat0, lon0, alt0, ell=EarthEllipsoid(), deg=True):
    """
     Input/output: units are METERS and DEGREES.
     if you specify NaN for srange, return value z will be NaN
    """
    # Origin of the local system in geocentric coordinates.
    x0, y0, z0 = geodetic2ecef(lat0, lon0, alt0, ell, deg=deg)
    # Convert Local Spherical AER to ENU
    e1, n1, u1 = aer2enu(az, el, srange, deg=deg)
    # Rotating ENU to ECEF
    dx, dy, dz = _enu2uvw(e1, n1, u1, lat0, lon0, deg=deg)
    # Origin + offset from origin equals position in ECEF
    return x0 + dx, y0 + dy, z0 + dz


def aer2enu(az, el, srange, deg=True):
    """
    input: azimuth, elevation [deg], slant range [m]
    output: East, North, Up [m]

    """
    if deg:
        el = radians(el)
        az = radians(az)

    r = srange * cos(el)
    return r * sin(az), r * cos(az), srange * sin(el)


def aer2geodetic(az, el, srange, lat0, lon0, alt0, deg=True):
    x, y, z = aer2ecef(az, el, srange, lat0, lon0, alt0, deg=deg)
    return ecef2geodetic(x, y, z, deg=deg)


def aer2ned(az, elev, slantRange, deg=True):
    e, n, u = aer2enu(az, elev, slantRange, deg=deg)
    return n, e, -u


def ecef2aer(x, y, z, lat0, lon0, h0, ell=EarthEllipsoid(), deg=True):
    xEast, yNorth, zUp = ecef2enu(x, y, z, lat0, lon0, h0, ell, deg=deg)
    return enu2aer(xEast, yNorth, zUp, deg=deg)


def ecef2enu(x, y, z, lat0, lon0, h0, ell=EarthEllipsoid(), deg=True):
    x0, y0, z0 = geodetic2ecef(lat0, lon0, h0, ell, deg=deg)
    return _uvw2enu(x - x0, y - y0, z - z0, lat0, lon0, deg=deg)


def _uvw2enu(u, v, w, lat0, lon0, deg):
    if deg:
        lat0 = radians(lat0)
        lon0 = radians(lon0)
    t = cos(lon0) * u + sin(lon0) * v
    East = -sin(lon0) * u + cos(lon0) * v
    Up = cos(lat0) * t + sin(lat0) * w
    North = -sin(lat0) * t + cos(lat0) * w
    return East, North, Up


def ecef2geodetic(x, y=None, z=None, ell=EarthEllipsoid(), deg=True):
    if y is None:
        x, y, z = _depack(x)
    """Algorithm is based on
    http://www.astro.uni.torun.pl/~kb/Papers/geod/Geod-BG.htm
    This algorithm provides a converging solution to the latitude
equation
    in terms of the parametric or reduced latitude form (v)
    This algorithm provides a uniform solution over all latitudes as it
does
    not involve division by cos(phi) or sin(phi)
    """
    ea = ell.a
    eb = ell.b
    rad = hypot(x, y)
# Constant required for Latitude equation
    rho = arctan2(eb * z, ea * rad)
# Constant required for latitude equation
    c = (ea**2 - eb**2) / hypot(ea * rad, eb * z)
# Starter for the Newtons Iteration Method
    vnew = arctan2(ea * z, eb * rad)
# Initializing the parametric latitude
    v = 0
    count = 0
    while (v != vnew).any() and count < 5:
        v = vnew.copy()
#%% Newtons Method for computing iterations
        vnew = v - ((2 * sin(v - rho) - c * sin(2 * v)) /
                    (2 * (cos(v - rho) - c * cos(2 * v))))
        count += 1

#%% Computing latitude from the root of the latitude equation
    lat = arctan2(ea * tan(vnew), eb)
    # by inspection
    lon = arctan2(y, x)

    alt = ((rad - ea * cos(vnew)) * cos(lat)) + \
        ((z - eb * sin(vnew)) * sin(lat))

    if deg:
        return degrees(lat), degrees(lon), alt
    else:
        return lat, lon, alt  # radians
"""
this is from PySatel and gives same result to EIGHT decimal places
def cbrt(x):
    if x >= 0:
        return pow(x, 1.0/3.0)
    else:
        return -pow(abs(x), 1.0/3.0)

def ecef2geodetic(x, y, z, ell=EarthEllipsoid(),deg=True):
    a = ell.a; b = ell.b
    esq = 6.69437999014*0.001
    e1sq = 6.73949674228*0.001
    r = hypot(x,y)
    Esq = a**2 - b**2
    F = 54 * b**2 * z**2
    G = r**2 + (1 - esq)* z**2 - esq*Esq
    C = (esq**2 *F* r**2)/(pow(G, 3))
    S = cbrt(1 + C + sqrt(C**2 + 2*C))
    P = F/(3* pow((S + 1/S + 1), 2)*G**2)
    Q = sqrt(1 + 2* esq**2 *P)
    r_0 =  -(P*esq*r)/(1 + Q) + sqrt(0.5* a**2 *(1 + 1.0/Q) - \
           P*(1 - esq)*z**2/(Q*(1 + Q)) - 0.5*P* r**2)
    U = sqrt(pow((r - esq*r_0), 2) + z**2)
    V = sqrt(pow((r - esq*r_0), 2) + (1 - esq)* z**2)
    Z_0 = b**2 *z/(a*V)
    alt = U*(1 - b**2/(a*V))
    lat = arctan((z + e1sq*Z_0)/r)
    lon = arctan2(y, x)

    if deg:
        return degrees(lat),degrees(lon),alt
    else:
        return lat, lon, alt #radians
"""


def ecef2ned(x, y, z, lat0, lon0, h0, ell=EarthEllipsoid(), deg=True):
    e, n, u = ecef2enu(x, y, z, lat0, lon0, h0, ell, deg=deg)
    return n, e, -u


def enu2aer(e, n, u, deg=True):
    """
    input: east, north, up [m]
    """
    r = hypot(e, n)
    slantRange = hypot(r, u)
    elev = arctan2(u, r)
    az = mod(arctan2(e, n), 2 * arctan2(0, -1))
    if deg:
        return degrees(az), degrees(elev), slantRange
    else:
        return az, elev, slantRange  # radians


def enu2ecef(e1, n1, u1, lat0, lon0, alt0, ell=EarthEllipsoid(), deg=True):
    x0, y0, z0 = geodetic2ecef(lat0, lon0, alt0, ell, deg=deg)
    dx, dy, dz = _enu2uvw(e1, n1, u1, lat0, lon0, deg=deg)
    return x0 + dx, y0 + dy, z0 + dz


def _enu2uvw(east, north, up, lat0, lon0, deg=True):
    if deg:
        lat0 = radians(lat0)
        lon0 = radians(lon0)
    t = cos(lat0) * up - sin(lat0) * north
    w = sin(lat0) * up + cos(lat0) * north

    u = cos(lon0) * t - sin(lon0) * east
    v = sin(lon0) * t + cos(lon0) * east
    return u, v, w


def enu2geodetic(e, n, u, lat0, lon0, h0,
                 ell=EarthEllipsoid(), deg=True):
    x, y, z = enu2ecef(e, n, u, lat0, lon0, h0, ell, deg=deg)
    return ecef2geodetic(x, y, z, ell, deg=deg)
#%% ECI functions
    """
    inputs:
    -------
    ece/ecef: a Nx3 vector of x,y,z triplets in the eci or ecef system [meters]
    : length N vector of datetime OR greenwich sidereal time angle [radians].

    Note: Conversion is idealized: doesn't consider nutations, perterbations,
    etc. like the IAU-76/FK5 or IAU-2000/2006 model-based conversions
    from ECI to ECEF
    """


def eci2geodetic(eci, t):
    """ a.k.a. eci2lla() """
    ecef = eci2ecef(eci, t)
    return ecef2geodetic(ecef[:, 0], ecef[:, 1], ecef[:, 2])


def aer2eci(az, el, srange, lat0, lon0, h0, t, ell=EarthEllipsoid(), deg=True):
    x, y, z = aer2ecef(az, el, srange, lat0, lon0, h0, ell, deg)
    return ecef2eci(column_stack((x, y, z)), t)


def eci2aer(eci, lat0, lon0, h0, t):
    ecef = eci2ecef(eci, t)
    return ecef2aer(ecef[:, 0], ecef[:, 1], ecef[:, 2], lat0, lon0, h0)


def eci2ecef(eci, t):
    """
    input t is either a datetime or float in radians

    """
    t = atleast_1d(t)
    if isinstance(t[0], datetime):
        gst = Time(t).sidereal_time('apparent', 'greenwich').radian
    else:
        gst = t
    assert isinstance(gst[0], float)  # must be in radians!

    eci = atleast_2d(eci)
    N, trip = eci.shape
    if eci.ndim > 2 or trip != 3:
        raise TypeError('eci triplets must be shape (N,3)')
    """ported from:
    https://github.com/dinkelk/astrodynamics/blob/master/rot3.m
    """
    ecef = empty_like(eci)

    for i in range(N):
        ecef[i, :] = _rottrip(gst[i]).dot(eci[i, :])
    return ecef


def ecef2eci(ecef, t):
    """
    input t is either a datetime or float in radians

    """
    t = atleast_1d(t)
    if isinstance(t[0], datetime):
        gst = Time(t).sidereal_time('apparent', 'greenwich').radian
    else:
        gst = t
    assert isinstance(gst[0], float)  # must be in radians!

    ecef = atleast_2d(ecef)
    N, trip = ecef.shape
    if ecef.ndim > 2 or trip != 3:
        raise TypeError('ecef triplets must be shape (N,3)')
    """ported from:
    https://github.com/dinkelk/astrodynamics/blob/master/rot3.m
    """
    eci = empty_like(ecef)
    for i in range(N):
        eci[i, :] = _rottrip(gst[i]).T.dot(
            ecef[i, :])  # this one is transposed
    return eci


def _rottrip(ang):
    ang = ang.squeeze()
    if ang.size > 1:
        raise TypeError('only one angle allowed at a time')
    """ported from:
    https://github.com/dinkelk/astrodynamics/blob/master/rot3.m
    """
    return array([[cos(ang),  sin(ang), 0],
                  [-sin(ang), cos(ang), 0],
                  [0,         0,        1]])
#==========================================================
#%%


def geodetic2aer(lat, lon, h, lat0, lon0, h0, ell=EarthEllipsoid(), deg=True):
    e, n, u = geodetic2enu(lat, lon, h, lat0, lon0, h0, ell, deg=deg)
    return enu2aer(e, n, u, deg=deg)


def geodetic2ecef(lat, lon, alt, ell=EarthEllipsoid(), deg=True):
    if deg:
        lat = radians(lat)
        lon = radians(lon)
    # radius of curvature of the prime vertical section
    N = get_radius_normal(lat, ell)
    # Compute cartesian (geocentric) coordinates given  (curvilinear) geodetic
    # coordinates.
    x = (N + alt) * cos(lat) * cos(lon)
    y = (N + alt) * cos(lat) * sin(lon)
    z = (N * (ell.b / ell.a)**2 + alt) * sin(lat)
    return x, y, z


def geodetic2enu(lat, lon, h, lat0, lon0, h0, ell=EarthEllipsoid(), deg=True):
    x1, y1, z1 = geodetic2ecef(lat, lon, h, ell, deg=deg)
    x2, y2, z2 = geodetic2ecef(lat0, lon0, h0, ell, deg=deg)
    dx = x1 - x2
    dy = y1 - y2
    dz = z1 - z2
    return _uvw2enu(dx, dy, dz, lat0, lon0, deg=deg)


def geodetic2ned(lat, lon, h, lat0, lon0, h0, ell=EarthEllipsoid(), deg=True):
    e, n, u = geodetic2enu(lat, lon, h, lat0, lon0, h0, ell, deg=deg)
    return n, e, -u


def ned2aer(n, e, d, deg=True):
    return enu2aer(e, n, -d, deg=deg)


def ned2ecef(n, e, d, lat0, lon0, h0, ell=EarthEllipsoid(), deg=True):
    return enu2ecef(e, n, -d, lat0, lon0, h0, ell, deg=deg)


def ned2geodetic(n, e, d, lat0, lon0, h0, ell=EarthEllipsoid(), deg=True):
    x, y, z = enu2ecef(e, n, -d, lat0, lon0, h0,  ell, deg=deg)
    return ecef2geodetic(x, y, z, ell, deg=deg)


def get_radius_normal(lat_radians, ell):
    a = ell.a
    b = ell.b
    return a**2 / sqrt(
        a**2 * (cos(lat_radians))**2 + b**2 *
        (sin(lat_radians))**2)


def _depack(x0):
    if x0.ndim > 2:
        raise TypeError('I expect Nx3 or 3XN triplets')
    m, n = x0.shape
    if m == 3:  # 3xN triplets
        x = x0[0, :]
        y = x0[1, :]
        z = x0[2, :]
    elif n == 3:  # Nx3 triplets
        x = x0[:, 0]
        y = x0[:, 1]
        z = x0[:, 2]
    else:
        raise TypeError('I expect an Nx3 or 3xN input of x,y,z')
    return x, y, z
