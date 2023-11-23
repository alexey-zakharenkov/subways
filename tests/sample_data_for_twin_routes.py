metro_samples = [
    {
        "name": (
            "Many different routes, both on naked stations and stop_positions/stop_areas/transfers, both linear and circular"  # noqa: E501
        ),
        "xml_file": "assets/twin_routes.osm",
        "cities_info": [
            {
                "num_stations": (3 + 4 + 5 + 5) + (3 + 6 + 7 + 5 + 6 + 7 + 7),
                "num_lines": 4 + 7,
                "num_interchanges": 0 + 2,
            },
        ],
        "twin_routes": {  # route master => twin routes
            "r10021": {"r151": "r153", "r153": "r151"},
            "r10022": {},
            "r10023": {},
            "C": {},
            "r10001": {"r201": "r202", "r202": "r201"},
            "r10002": {},
            "r10003": {"r205": "r206", "r206": "r205"},
            "r10004": {},
            "r10005": {},
            "r10006": {},
            "C3": {},
        },
        "errors": [],
        "warnings": [],
        "notices": [
            'Route does not have a return direction (relation 154, "02: 4-3")',
            'Route does not have a return direction (relation 155, "02: 1-3")',
            'Route does not have a return direction (relation 156, "02: 2-4")',
            'Route does not have a return direction (relation 157, "02: 4-1")',
            'Route does not have a return direction (relation 158, "02: 1-3 (2)")',  # noqa: E501
            'Only one route in route_master. Please check if it needs a return route (relation 159, "C: 1-2-3-4-5-1")',  # noqa: E501
            'Stop Station 4 (3.0, 0.0) is included into the r205 but not included into r206 (relation 206, "3: 7-6-5-3-2-1")',  # noqa: E501
            'Route does not have a return direction (relation 207, "4: 4-3-2-1")',  # noqa: E501
            'Route does not have a return direction (relation 208, "4: 1-2-3-4")',  # noqa: E501
            'Route does not have a return direction (relation 209, "5: 1-2-3-5-6-7")',  # noqa: E501
            'Route does not have a return direction (relation 210, "5: 6-5-3-2-1")',  # noqa: E501
            'Only one route in route_master. Please check if it needs a return route (relation 213, "C3: 1-2-3-5-6-7-8-1")',  # noqa: E501
        ],
    },
    {
        "name": "Twin routes diverging for some extent",
        "xml_file": "assets/twin_routes_with_divergence.osm",
        "cities_info": [
            {
                "num_stations": (22 + 22 + 21 + 21) * 2,
                "num_lines": 4 * 2,
                "num_interchanges": 0,
            },
        ],
        "twin_routes": {  # route master => twin routes
            "r1101": {"r101": "r102", "r102": "r101"},
            "r1102": {"r103": "r104", "r104": "r103"},
            "r1103": {"r105": "r106", "r106": "r105"},
            "r1104": {"r107": "r108", "r108": "r107"},
            "r1201": {"r201": "r202", "r202": "r201"},
            "r1202": {"r203": "r204", "r204": "r203"},
            "r1203": {"r205": "r206", "r206": "r205"},
            "r1204": {"r207": "r208", "r208": "r207"},
        },
        "errors": [],
        "warnings": [],
        "notices": [
            'Should there be one stoparea or a transfer between Station 11 (0.1, 0.0) and Station 11(1) (0.1, 0.0003)? (relation 101, "1: 1-...-9-10-11-...-20")',  # noqa: E501
            'Should there be one stoparea or a transfer between Station 10 (0.09, 0.0) and Station 10(1) (0.09, 0.0003)? (relation 101, "1: 1-...-9-10-11-...-20")',  # noqa: E501
            'Stop Station 10 (0.09, 0.0) is included into the r105 but not included into r106 (relation 106, "3: 20-...-12-11(1)-9-...-1")',  # noqa: E501
            'Should there be one stoparea or a transfer between Station 11 (0.1, 0.0) and Station 11(1) (0.1, 0.0003)? (relation 105, "3: 1-...-9-10-11-...-20")',  # noqa: E501
            'Stop Station 10 (0.09, 0.0) is included into the r107 but not included into r108 (relation 108, "4: 20-...12-11(2)-9-...-1")',  # noqa: E501
            'Should there be one stoparea or a transfer between Station 11 (0.1, 0.0) and Station 11(1) (0.1, 0.0003)? (relation 201, "11: 1-...-9-10-11-...-20")',  # noqa: E501
            'Should there be one stoparea or a transfer between Station 10 (0.09, 0.0) and Station 10(1) (0.09, 0.0003)? (relation 201, "11: 1-...-9-10-11-...-20")',  # noqa: E501
            'Stop Station 10 (0.09, 0.0) is included into the r205 but not included into r206 (relation 206, "13: 20-...-12-11(1)-9-...-1")',  # noqa: E501
            'Should there be one stoparea or a transfer between Station 11 (0.1, 0.0) and Station 11(1) (0.1, 0.0003)? (relation 205, "13: 1-...-9-10-11-...-20")',  # noqa: E501
        ],
    },
]
