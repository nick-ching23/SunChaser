import requests

class Electricity_Maps:
    
    def __init__(self):
        self.oregon_carbon_intensity = self.get_oregon_carbon_intensity()                  # low carbon region
        self.texas_carbon_intensity = self.get_texas_carbon_intensity()                    # medium carbon region
        self.south_carolina_carbon_intensity = self.get_south_carolina_carbon_intensity()  # high carbon region


    def get_texas_carbon_intensity(self):
        # ERCOT - Texas
        response = requests.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=US-TEX-ERCO",
            headers={"auth-token": f"pjNv2UzTRbP8JXRMN26n"},
        )

        carbon_data = response.json()
        return carbon_data['carbonIntensity']

    def get_oregon_carbon_intensity(self):
        # Bonneville power station (Portland Oregon)
        response = requests.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=US-NW-BPAT",
            headers={"auth-token": f"Ksa4UyL3ywuJ81v0Mpyx"},
        )

        carbon_data = response.json()
        return carbon_data['carbonIntensity']

    def get_south_carolina_carbon_intensity(self):
        # South Carolina Public Service Authority (Charleston SC)
        response = requests.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=US-CAR-SC",
            headers={"auth-token": f"THa7vuk5iCJXlAJ1k9Pt"},
        )

        carbon_data = response.json()
        return carbon_data['carbonIntensity']
    
