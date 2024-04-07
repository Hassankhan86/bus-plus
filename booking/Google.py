from geopy.geocoders import Nominatim



class GoogleAPI:
    def __init__(self) -> None:
        pass
    def get_country_from_address(self, address):
        geolocator = Nominatim(user_agent="country_checker")
        location = geolocator.geocode(address)
        if location:
            return location.address.split(",")[-1].strip()
        else:
            return None
        """
        try:
            google = GoogleAPI()
            pickup_country = google.get_country_from_address(pickup)
            destination_country = google.get_country_from_address(destination)
            if pickup_country.lower() is not COUNTRY:
                messages.add_message(request, messages.INFO, f"We do not have  Services  in {pickup_country}")
                pickup = None
            if destination_country.lower() is not COUNTRY:
                messages.add_message(request, messages.INFO, f"We do not have  Services  in {destination_country}")
                destination = None
        except:
            pass
        
        """
    