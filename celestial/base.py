class CelestialBody:
    """
    Base class for all celestial bodies. Provides a common interface for retrieving and enhancing astronomical data.
    Subclasses should implement or override the methods as needed for each specific body.
    """
    def __init__(self, name: str):
        self.name = name  # Name of the celestial body

    def get_basic_info(self, observer):
        """
        Retrieve basic astronomical information using ephem for the given observer.
        Should be implemented by subclasses.
        """
        raise NotImplementedError

    def enhance_with_skyfield(self, body_data, current_time, lat, lon, has_location):
        """
        Optionally enhance the data using skyfield for more precise calculations.
        """
        pass

    def enhance_with_astropy(self, body_data, current_time, lat, lon, has_location):
        """
        Optionally enhance the data using astropy for advanced calculations (e.g., precise constellation).
        """
        pass

    def add_rise_set_times(self, body_data, observer, body, has_location):
        """
        Optionally add rise and set times to the data if location is provided.
        """
        pass 