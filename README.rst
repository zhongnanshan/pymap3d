.. image:: https://codeclimate.com/github/scienceopen/pymap3d/badges/gpa.svg
   :target: https://codeclimate.com/github/scienceopen/pymap3d
   :alt: Code Climate
.. image:: https://travis-ci.org/scienceopen/pymap3d.svg?branch=master
    :target: https://travis-ci.org/scienceopen/pymap3d
.. image:: https://coveralls.io/repos/scienceopen/pymap3d/badge.svg
    :target: https://coveralls.io/r/scienceopen/pymap3d

==================================
Python 3-D coordinate conversions
==================================

Python coordinate conversions, following convention of several popular Matlab routines.

Usage
=====
a few quick examples::

   from pymap3d.coordconv3d import *
   
   lat,lon,alt = eci2geodetic(eci,t)
   az,el,range = geodetic2aer(lat,lon,alt,42,-82,0)

Functions
==========
Popular mapping toolbox functions ported to Python include::

 aer2ecef  aer2enu  aer2geodetic  aer2ned
  ecef2aer  ecef2enu  ecef2enuv  ecef2geodetic  ecef2ned  ecef2nedv  ecef2eci
  eci2ecef
  enu2aer  enu2ecef  enu2ecefv  enu2geodetic
  geodetic2aer  geodetic2ecef  geodetic2enu  geodetic2ned
  ned2aer  ned2ecef  ned2ecefv  ned2geodetic
  vreckon vdist
  azel2radec radec2azel


Installation
============
::

  python setup.py develop


Caveats
=======
Atmospheric effects neglected in all functions not invoking AstroPy.
Planetary perturbations and nutation etc. not fully considered.
