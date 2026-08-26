# Routing notes

The prototype runs an OR-Tools Capacitated Vehicle Routing Problem (CVRP) for depot -> pickup stops -> buyer. It checks:

- pickup list and vehicle list are non-empty;
- total pickup demand fits the available fleet;
- no individual pickup exceeds the largest available vehicle;
- solver feasibility within a three-second search limit;
- optional delivery deadline against a labeled 42 km/h demo duration assumption.

Distance is currently a derived Haversine value multiplied by a road factor. This is intentional: the API returns `derived-haversine-demo` and classifies route coordinates, matrix, and output as synthetic/derived. It is not a live road-navigation result.

For production, generate a distance-and-duration matrix from a provider compliant with its terms of use, cache provider responses, include tolls/vehicle restrictions/cold-chain requirements, and pass a map-matched route geometry to the frontend. Validate driver hours, service time, dynamic vehicle availability, and road-closure events before dispatch.
