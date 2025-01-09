import folium


def add_route_with_points(m, route_coords, line_color='blue', line_opacity=0.8, dot_color='blue', dot_radius=4):
    """Add route line and points to map"""
    # Add the route line
    folium.PolyLine(
        route_coords,
        weight=4,
        color=line_color,
        opacity=line_opacity
    ).add_to(m)

    # Add dots for each point
    for lat, lon in route_coords:
        folium.CircleMarker(
            location=[lat, lon],
            radius=dot_radius,
            color=dot_color,
            fill=True,
            fillOpacity=1.0
        ).add_to(m)


def create_route_map(
    route_points, start_name, end_name, nearby_stations=None, all_stations=None, filename='route_map.html'
):
    """Create and save route map"""
    # Extract coordinates
    latitudes = [point['lat'] for point in route_points]
    longitudes = [point['lng'] for point in route_points]
    route_coords = [[point['lat'], point['lng']] for point in route_points]

    # Create map
    center_lat = sum(latitudes) / len(latitudes)
    center_lng = sum(longitudes) / len(longitudes)
    m = folium.Map(location=[center_lat, center_lng], zoom_start=5)

    # Add route and points
    add_route_with_points(m, route_coords)

    # Add start/end markers
    folium.Marker(route_coords[0], popup=start_name).add_to(m)
    folium.Marker(route_coords[-1], popup=end_name).add_to(m)

    # Create set of nearby station IDs for quick lookup
    nearby_station_ids = {station['locationId'] for station in (nearby_stations or [])}

    # Add all fuel stations not near the route as red markers
    if all_stations:
        for station in all_stations:
            # Skip if we'll add it later as a nearby station
            if station['locationId'] in nearby_station_ids:
                continue

            popup_content = f"""
                <b>Location ID:</b> {station['locationId']}<br>
                <b>Address:</b> {station['address']}<br>
                <b>Diesel Price:</b> ${station.get('dieselPrice', 'N/A')}
            """
            folium.Marker(
                location=[float(station['lat']), float(station['lon'])],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color='red', icon='gas', prefix='fa')
            ).add_to(m)

    # Add nearby stations with green icons
    if nearby_stations:
        for station in nearby_stations:
            popup_content = f"""
                <b>Location ID:</b> {station['locationId']}<br>
                <b>Address:</b> {station['address']}<br>
                <b>Diesel Price:</b> ${station.get('dieselPrice', 'N/A')}
            """
            folium.Marker(
                location=[float(station['lat']), float(station['lon'])],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color='green', icon='gas', prefix='fa')
            ).add_to(m)

    # Save map
    m.save(filename)
    return m
