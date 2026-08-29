import joblib
import pandas as pd
import os
import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from app.core.config import settings

class DemandModel:
    def __init__(self):
        self.model_path = os.path.join(settings.models_dir, "demand_rf_model.joblib")
        self.model = None
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
    
    def predict(self, crop_id: str, region: str, horizon_days: int):
        if not self.model:
            # Fallback heuristic if not trained
            return {"level": "HIGH" if horizon_days < 10 else "MEDIUM", "confidence": 0.65}
        
        # Real inference would construct a feature vector here.
        # df = pd.DataFrame([{"crop_encoded": ..., "region_encoded": ..., "horizon": horizon_days}])
        # pred = self.model.predict(df)
        return {"level": "HIGH", "confidence": 0.85}

def calculate_distance(lat1, lon1, lat2, lon2):
    # Haversine distance
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

class RoutingModel:
    def optimize(self, start_loc, stops, capacity):
        all_locs = [start_loc] + stops
        num_locs = len(all_locs)
        
        dist_matrix = []
        for i in range(num_locs):
            row = []
            for j in range(num_locs):
                if i == j:
                    row.append(0)
                else:
                    dist = calculate_distance(
                        all_locs[i].latitude, all_locs[i].longitude,
                        all_locs[j].latitude, all_locs[j].longitude
                    )
                    row.append(int(dist * 1000)) # OR-tools uses integers
            dist_matrix.append(row)

        manager = pywrapcp.RoutingIndexManager(num_locs, 1, 0)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return dist_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

        solution = routing.SolveWithParameters(search_parameters)
        if solution:
            index = routing.Start(0)
            route = []
            total_dist = 0
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                if node_index > 0: # Skip start node in output
                    route.append(all_locs[node_index].location_id)
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                total_dist += routing.GetArcCostForVehicle(previous_index, index, 0)
            return {"route": route, "distance_km": total_dist / 1000.0}
        return {"route": [s.location_id for s in stops], "distance_km": 0.0}
