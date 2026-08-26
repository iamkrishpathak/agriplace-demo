from typing import Any

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from backend.app.schemas import RouteLocation, VehicleCapacity
from backend.app.services.geo import derived_road_km


def _distance_matrix_meters(locations: list[RouteLocation]) -> list[list[int]]:
    matrix: list[list[int]] = []
    for src in locations:
        row = []
        for dst in locations:
            row.append(int(derived_road_km(src.latitude, src.longitude, dst.latitude, dst.longitude) * 1000))
        matrix.append(row)
    return matrix


def _route_distance_km(route: list[int], matrix: list[list[int]]) -> float:
    return round(sum(matrix[route[i]][route[i + 1]] for i in range(len(route) - 1)) / 1000, 2)


def optimize_cvrp(
    *,
    depot: RouteLocation,
    pickups: list[RouteLocation],
    buyer: RouteLocation,
    vehicles: list[VehicleCapacity],
    cost_per_km: float = 24.0,
    deadline_hours: float | None = None,
) -> dict[str, Any]:
    if not pickups:
        return {
            "feasible": False,
            "reason": "At least one pickup stop is required.",
            "routes": [],
        }
    if not vehicles:
        return {
            "feasible": False,
            "reason": "At least one vehicle is required to optimize a route.",
            "routes": [],
        }

    total_demand = int(sum(p.quantity_kg for p in pickups))
    total_capacity = int(sum(vehicle.capacity_kg for vehicle in vehicles))
    max_capacity = max(vehicle.capacity_kg for vehicle in vehicles)
    if total_demand > total_capacity:
        return {
            "feasible": False,
            "reason": "Vehicle capacity exceeded. Split into more trips or assign a larger vehicle.",
            "total_demand_kg": total_demand,
            "total_capacity_kg": total_capacity,
            "split_required": True,
            "routes": [],
        }
    if any(p.quantity_kg > max_capacity for p in pickups):
        return {
            "feasible": False,
            "reason": "At least one pickup quantity exceeds the largest vehicle capacity.",
            "split_required": True,
            "routes": [],
        }

    locations = [depot, *pickups, buyer]
    buyer_index = len(locations) - 1
    matrix = _distance_matrix_meters(locations)
    demands = [0, *[int(p.quantity_kg) for p in pickups], 0]
    vehicle_capacities = [int(v.capacity_kg) for v in vehicles]

    manager = pywrapcp.RoutingIndexManager(
        len(locations),
        len(vehicles),
        [0 for _ in vehicles],
        [buyer_index for _ in vehicles],
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        vehicle_capacities,
        True,
        "Capacity",
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = 3
    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return {
            "feasible": False,
            "reason": "No feasible route found within solver time limit.",
            "total_demand_kg": total_demand,
            "total_capacity_kg": total_capacity,
            "routes": [],
        }

    routes = []
    optimized_distance_km = 0.0
    for vehicle_id, vehicle in enumerate(vehicles):
        if not routing.IsVehicleUsed(solution, vehicle_id):
            continue
        index = routing.Start(vehicle_id)
        route_node_indices = []
        route_load = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_node_indices.append(node_index)
            route_load += demands[node_index]
            index = solution.Value(routing.NextVar(index))
        route_node_indices.append(manager.IndexToNode(index))
        distance_km = _route_distance_km(route_node_indices, matrix)
        optimized_distance_km += distance_km
        routes.append(
            {
                "vehicle_id": vehicle.id,
                "vehicle_label": vehicle.label,
                "capacity_kg": vehicle.capacity_kg,
                "load_kg": route_load,
                "distance_km": distance_km,
                "stops": [
                    {
                        "index": node_index,
                        "id": locations[node_index].id,
                        "label": locations[node_index].label,
                        "stop_type": locations[node_index].stop_type,
                        "quantity_kg": locations[node_index].quantity_kg,
                        "latitude": locations[node_index].latitude,
                        "longitude": locations[node_index].longitude,
                    }
                    for node_index in route_node_indices
                ],
            }
        )

    original_indices = [0, *range(1, buyer_index), buyer_index]
    original_distance_km = _route_distance_km(list(original_indices), matrix)
    optimized_distance_km = round(optimized_distance_km, 2)
    saved_distance_km = round(max(0.0, original_distance_km - optimized_distance_km), 2)
    estimated_cost_saving = round(saved_distance_km * cost_per_km, 2)
    estimated_duration_hours = round(optimized_distance_km / 42, 1)
    on_time_feasible = deadline_hours is None or estimated_duration_hours <= deadline_hours

    return {
        "feasible": True,
        "provider": "derived-haversine-demo; replace matrix with OSRM/OpenRouteService in production",
        "algorithm": "OR-Tools Capacitated Vehicle Routing Problem",
        "total_demand_kg": total_demand,
        "total_capacity_kg": total_capacity,
        "original_distance_km": original_distance_km,
        "optimized_distance_km": optimized_distance_km,
        "saved_distance_km": saved_distance_km,
        "estimated_cost_saving": estimated_cost_saving,
        "estimated_duration_hours": estimated_duration_hours,
        "on_time_feasible": on_time_feasible,
        "routes": routes,
        "matrix_units": {"distance": "meters", "duration": "derived at 42 km/h demo assumption"},
        "data_classification": {
            "coordinates": "SYNTHETIC demo coordinates",
            "distance_matrix": "DERIVED",
            "route": "DERIVED",
        },
    }
