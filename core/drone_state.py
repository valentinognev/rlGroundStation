from dataclasses import dataclass
import random

@dataclass
class DroneSelfState:
    # Mimicking the C struct fields
    id: int
    lat: float
    lon: float
    alt: float
    velocity_north: float
    velocity_east: float
    velocity_down: float
    heading: float
    sm_current_stat: int
    battery_precentages: int
    drones_keep_alive: int  # 4 bits (represented as int)
    gps_3d_fix: int         # 1 bit (represented as int)

    @staticmethod
    def create_from_viz_data(id_num, lat, lon, heading):
        """
        Factory method to create a struct from basic viz data, 
        filling the rest with 'recorded' garbage/random data.
        """
        return DroneSelfState(
            id=id_num,
            lat=lat,
            lon=lon,
            heading=heading,
            # Random / Mock Data for the rest
            alt=random.uniform(10.0, 50.0),
            velocity_north=random.uniform(-5.0, 5.0),
            velocity_east=random.uniform(-5.0, 5.0),
            velocity_down=random.uniform(-0.5, 0.5),
            sm_current_stat=random.randint(0, 9),
            battery_precentages=random.randint(20, 100),
            drones_keep_alive=15, # 1111 in binary
            gps_3d_fix=1
        )