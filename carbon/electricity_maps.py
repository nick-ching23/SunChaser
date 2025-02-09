import requests

class ElectricityMaps:
    
    def __init__(self):
        self.region_map = {
            "oregon": { #low
                "url": "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=US-NW-BPAT",
                "token": "Ksa4UyL3ywuJ81v0Mpyx",
            },
            "texas": { #mid
                "url": "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=US-TEX-ERCO",
                "token": "pjNv2UzTRbP8JXRMN26n",
            },
            "south_carolina": { #high
                "url": "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=US-CAR-SC",
                "token": "THa7vuk5iCJXlAJ1k9Pt",
            },
        }

    def get_carbon_intensity(self, region):
        response = requests.get(
            self.region_map[region]['url'],
            headers={"auth-token": self.region_map[region]['token']},
        )

        carbon_data = response.json()
        return carbon_data['carbonIntensity']

    def get_all_carbon_intensities(self):
        return {
            "oregon": self.get_carbon_intensity('oregon'),
            "texas": self.get_carbon_intensity('texas'),
            "south_carolina": self.get_carbon_intensity('south_carolina'),
        }