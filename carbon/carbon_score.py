from typing import Tuple

from ElectricityMaps import ElectricityMaps
import subprocess

class CarbonScoreCalculator:
    
    CLUSTERS = [
    "gke_sunchaser-450121_us-west1-a_sun-chaser-oregon",
    "gke_sunchaser-450121_us-south1-a_sun-chaser-texas",
    "gke_sunchaser-450121_us-east1-b_sun-chaser-south-carolina",
    ]
        
    def parse_cpu(self, cpu_str):
        cpu_str = cpu_str.strip().lower()
        if cpu_str.endswith("m"):
            return float(cpu_str[:-1])

    def parse_cluster_pod(self, cluster_str):
        lines = cluster_str.strip().splitlines()
        if len(lines) < 2:
            print("No pods found or invalid output from kubectl top.")
            return
        
        total_cpu_millicores = 0.0

        for line in lines[1:]:  # skip header
            columns = line.split()
            if len(columns) < 4:
                continue
            cpu_str = columns[2]  # e.g. "50m" or "2"

            cpu_m = self.parse_cpu(cpu_str)
            total_cpu_millicores += cpu_m
        
        return total_cpu_millicores    

    def retrieve_usage_info(self):
        
        region_usage = []
        
        for ctx in self.CLUSTERS:
            cmd = ["kubectl", "--context", ctx, "top", "pods", "-A"]
            try:
                output = subprocess.check_output(cmd, text=True)
                #print(output)
                # parse the number of millicores and process
                region_usage.append(self.parse_cluster_pod(output))
            except subprocess.CalledProcessError as e:
                print(f"Error running kubectl top for {ctx}: {e}")
        
        return region_usage if region_usage is not None else [0,0,0]
    
    def calculate_carbon_score(self) -> Tuple:
        em = ElectricityMaps()
           
        oregon_carbon_intensity= em.get_carbon_intensity("oregon")
        texas_carbon_intensity = em.get_carbon_intensity("texas")
        south_carolina_carbon_intensity = em.get_carbon_intensity(
            "south_carolina"
        )
        
        region_usage = self.retrieve_usage_info()
        region_intensity = [oregon_carbon_intensity, texas_carbon_intensity, south_carolina_carbon_intensity]

        for pair in zip(region_usage, region_intensity): 
            wattage = round(1.1 + (13.9 * pair[0]/1000), 3)
            carbon_emission_score = round(wattage/1000 * pair[1], 3)
            print(
                f"{wattage} Wattage, {carbon_emission_score} Carbon "
                f"Emission Score"
            )
            return (wattage, carbon_emission_score)

