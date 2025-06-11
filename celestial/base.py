from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import ephem
from . import utils

class CelestialBody:
    """
    Base class for all celestial bodies. Provides a common interface for retrieving and enhancing astronomical data.
    Subclasses should implement or override the methods as needed for each specific body.
    """
    def __init__(self, name: str):
        self.name = name  # Name of the celestial body
        self.ephem_body = None  # PyEphem object to be set by subclass
        self.skyfield_body = None  # Skyfield object to be set by subclass

    def get_basic_info(self, observer) -> Dict[str, Any]:
        """
        Retrieve basic astronomical information using ephem for the given observer.
        Should be implemented by subclasses.
        
        Parameters:
            observer: PyEphem observer object
            
        Returns:
            Dictionary containing basic astronomical data
        """
        raise NotImplementedError

    def enhance_with_skyfield(self, body_data: Dict[str, Any], current_time: datetime, 
                             lat: Optional[float], lon: Optional[float], has_location: bool) -> None:
        """
        Enhance the data using skyfield for more precise calculations.
        Includes proper topocentric corrections, time scale handling, and aberration/nutation.
        
        Parameters:
            body_data: Dictionary to be enhanced with additional data
            current_time: Current UTC time
            lat: Observer's latitude (if available)
            lon: Observer's longitude (if available)
            has_location: Boolean indicating if location is provided
        """
        try:
            # Get time scales
            time_scales = utils.get_time_scales(current_time)
            t_utc = time_scales['utc']
            t_tt = time_scales['tt']  # Terrestrial Time - for Earth-based observations
            t_tdb = time_scales['tdb']  # Barycentric Dynamical Time - for solar system calculations
            
            # Add time scale information to response
            body_data["time_scales"] = {
                "utc": current_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "tt": t_tt.utc_strftime("%Y-%m-%d %H:%M:%S TT"),
                "tdb": t_tdb.utc_strftime("%Y-%m-%d %H:%M:%S TDB")
            }
            
            # Geocentric calculations (from Earth's center)
            earth_at_t = utils.earth.at(t_tdb)  # Use TDB for solar system positions
            body_at_t = earth_at_t.observe(self.skyfield_body).apparent()  # Apply aberration and nutation
            
            # Get astrometric position (ICRS coordinates)
            ra, dec, distance = body_at_t.radec()
            
            # Add celestial coordinates with improved formatting
            body_data["celestial_coordinates"] = utils.radec_to_dict(ra, dec)
            
            # Add more precise distance measurement
            body_data["distance"]["au"] = round(distance.au, 6)
            body_data["distance"]["km"] = int(distance.km)
            body_data["distance"]["light_time_seconds"] = round(distance.light_seconds, 2)
            
            # Add uncertainty information
            body_data["precision"] = {
                "position_uncertainty_arcsec": 0.01,  # Approximate value, depends on ephemeris
                "time_system": "TDB",
                "reference_frame": "ICRS",
                "ephemeris": utils.eph.names[0]  # Name of the ephemeris file used
            }
            
            # Add topocentric calculations if location is provided
            if has_location:
                # Get topocentric position (from observer's location on Earth)
                topo_pos, observer_at_t = utils.get_topocentric_position(lat, lon, t_tt, self.skyfield_body)
                
                # Get topocentric RA/Dec
                topo_ra, topo_dec, topo_distance = topo_pos.radec()
                body_data["topocentric_coordinates"] = utils.radec_to_dict(topo_ra, topo_dec)
                
                # Get altitude and azimuth with higher precision
                alt, az, _ = topo_pos.altaz()
                body_data["topocentric_position"] = utils.altaz_to_dict(alt, az)
                
                # Add difference between geocentric and topocentric positions
                body_data["geocentric_vs_topocentric"] = {
                    "ra_difference_arcsec": round((ra.hours - topo_ra.hours) * 15 * 3600, 2),
                    "dec_difference_arcsec": round((dec.degrees - topo_dec.degrees) * 3600, 2),
                    "distance_difference_km": round(distance.km - topo_distance.km, 2)
                }
        except Exception as e:
            body_data["skyfield_error"] = str(e)

    def enhance_with_astropy(self, body_data: Dict[str, Any], current_time: datetime, 
                            lat: Optional[float], lon: Optional[float], has_location: bool) -> None:
        """
        Enhance the data using astropy for advanced calculations.
        
        Parameters:
            body_data: Dictionary to be enhanced with additional data
            current_time: Current UTC time
            lat: Observer's latitude (if available)
            lon: Observer's longitude (if available)
            has_location: Boolean indicating if location is provided
        """
        pass  # To be implemented by subclasses

    def add_rise_set_times(self, body_data: Dict[str, Any], observer, has_location: bool) -> None:
        """
        Add rise and set times to the data if location is provided.
        
        Parameters:
            body_data: Dictionary to be enhanced with rise/set times
            observer: PyEphem observer object
            has_location: Boolean indicating if location is provided
        """
        pass  # To be implemented by subclasses 