import threading
import time
from electricity_maps import ElectricityMaps

class CarbonInfoRetriever:
    def __init__(self):
        self.map = ElectricityMaps()
        self.info = []
        self.running = False
        self.thread = None

    def collect_data(self):
        """Function to collect carbon intensity data every 2 minutes."""
        while self.running:
            self.info.append(self.map.get_all_carbon_intensities())
            time.sleep(120)

    def start_monitoring(self):
        """Start data collection in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.collect_data, daemon=True)
            self.thread.start()

    def stop_monitoring(self):
        """Stop the monitoring process."""
        self.running = False
        if self.thread:
            self.thread.join()
