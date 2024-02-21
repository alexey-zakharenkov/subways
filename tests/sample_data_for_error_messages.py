metro_samples = [
    {
        "name": "No errors",
        "xml": """<?xml version='1.0' encoding='UTF-8'?>
<osm version='0.6' generator='JOSM'>
  <node id='1' version='1' lat='0.0' lon='0.0'>
    <tag k='name' v='Station 1' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='2' version='1' lat='0.0' lon='1.0'>
    <tag k='name' v='Station 2' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='2' role='' />
    <member type='node' ref='1' role='' />
    <tag k='name' v='Backward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='3' version='1'>
    <member type='relation' ref='1' role='' />
    <member type='relation' ref='2' role='' />
    <tag k='ref' v='1' />
    <tag k='colour' v='red' />
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "cities_info": [
            {
                "num_stations": 2,
                "num_lines": 1,
                "num_light_lines": 0,
                "num_interchanges": 0,
            },
        ],
        "errors": [],
        "warnings": [],
        "notices": [],
    },
    {
        "name": "Bad station order",
        "xml": """<?xml version='1.0' encoding='UTF-8'?>
<osm version='0.6' generator='JOSM'>
  <node id='1' version='1' lat='0.0' lon='0.0'>
    <tag k='name' v='Station 1' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='2' version='1' lat='0.0' lon='1.0'>
    <tag k='name' v='Station 2' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='3' version='1' lat='0.0' lon='2.0'>
    <tag k='name' v='Station 3' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='4' version='1' lat='0.0' lon='3.0'>
    <tag k='name' v='Station 4' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='4' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='4' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='1' role='' />
    <tag k='name' v='Backward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='3' version='1'>
    <member type='relation' ref='1' role='' />
    <member type='relation' ref='2' role='' />
    <tag k='ref' v='1' />
    <tag k='colour' v='red' />
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "cities_info": [
            {
                "num_stations": 4,
            },
        ],
        "errors": [
            'Angle between stops around "Station 3" (2.0, 0.0) is too narrow, 0 degrees (relation 1, "Forward")',  # noqa: E501
            'Angle between stops around "Station 2" (1.0, 0.0) is too narrow, 0 degrees (relation 1, "Forward")',  # noqa: E501
        ],
        "warnings": [],
        "notices": [],
    },
    {
        "name": "Angle < 20 degrees",
        "xml": """<?xml version='1.0' encoding='UTF-8'?>
<osm version='0.6' generator='JOSM'>
  <node id='1' version='1' lat='0.0' lon='0.0'>
    <tag k='name' v='Station 1' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='2' version='1' lat='0.0' lon='1.0'>
    <tag k='name' v='Station 2' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='3' version='1' lat='0.2' lon='0.0'>
    <tag k='name' v='Station 3' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='3' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='1' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Backward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='3' version='1'>
    <member type='relation' ref='1' role='' />
    <member type='relation' ref='2' role='' />
    <tag k='ref' v='1' />
    <tag k='colour' v='red' />
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "cities_info": [
            {
                "num_stations": 3,
            },
        ],
        "errors": [
            'Angle between stops around "Station 2" (1.0, 0.0) is too narrow, 11 degrees (relation 1, "Forward")',  # noqa: E501
            'Angle between stops around "Station 2" (1.0, 0.0) is too narrow, 11 degrees (relation 2, "Backward")',  # noqa: E501
        ],
        "warnings": [],
        "notices": [],
    },
    {
        "name": "Angle between 20 and 45 degrees",
        "xml": """<?xml version='1.0' encoding='UTF-8'?>
<osm version='0.6' generator='JOSM'>
  <node id='1' version='1' lat='0.0' lon='0.0'>
    <tag k='name' v='Station 1' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='2' version='1' lat='0.0' lon='1.0'>
    <tag k='name' v='Station 2' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='3' version='1' lat='0.5' lon='0.0'>
    <tag k='name' v='Station 3' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='3' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='1' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Backward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='3' version='1'>
    <member type='relation' ref='1' role='' />
    <member type='relation' ref='2' role='' />
    <tag k='ref' v='1' />
    <tag k='colour' v='red' />
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "cities_info": [
            {
                "num_stations": 3,
            },
        ],
        "errors": [],
        "warnings": [],
        "notices": [
            'Angle between stops around "Station 2" (1.0, 0.0) is too narrow, 27 degrees (relation 1, "Forward")',  # noqa: E501
            'Angle between stops around "Station 2" (1.0, 0.0) is too narrow, 27 degrees (relation 2, "Backward")',  # noqa: E501
        ],
    },
    {
        "name": "Unordered stops provided each angle > 45 degrees",
        "xml": """<?xml version='1.0' encoding='UTF-8'?>
<osm version='0.6' generator='JOSM'>
  <node id='1' version='1' lat='0.0' lon='0.0'>
    <tag k='name' v='Station 1' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='2' version='1' lat='0.0' lon='1.0'>
    <tag k='name' v='Station 2' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='3' version='1' lat='0.5' lon='0.0'>
    <tag k='name' v='Station 3' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='4' version='1' lat='1.0' lon='1.0'>
    <tag k='name' v='Station 4' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <way id='1' version='1'>
    <nd ref='1' />
    <nd ref='2' />
    <nd ref='3' />
    <tag k='railway' v='subway' />
  </way>
  <way id='2' version='1'>
    <nd ref='3' />
    <nd ref='4' />
    <tag k='railway' v='subway' />
  </way>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='4' role='' />
    <member type='way' ref='1' role='' />
    <member type='way' ref='2' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='4' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='1' role='' />
    <member type='way' ref='2' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Backward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='3' version='1'>
    <member type='relation' ref='1' role='' />
    <member type='relation' ref='2' role='' />
    <tag k='ref' v='1' />
    <tag k='colour' v='red' />
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "cities_info": [
            {
                "num_stations": 4,
            },
        ],
        "errors": [
            'Stops on tracks are unordered near "Station 2" (1.0, 0.0) (relation 1, "Forward")',  # noqa: E501
            'Stops on tracks are unordered near "Station 3" (0.0, 0.5) (relation 2, "Backward")',  # noqa: E501
        ],
        "warnings": [],
        "notices": [],
    },
    {
        "name": (
            "Many different route masters, both on naked stations and "
            "stop_positions/stop_areas/transfers, both linear and circular"
        ),
        "xml_file": "assets/route_masters.osm",
        "cities_info": [
            {
                "num_stations": (3 + 3 + 3 + 5 + 3 + 3 + 4 + 3)
                + (3 + 3 + 3 + 3 + 3 + 3 + 4),
                "num_lines": 8 + 7,
                "num_interchanges": 0 + 1,
            },
        ],
        "errors": [
            'Only one route in route_master. Please check if it needs a return route (relation 162, "03: 1-2-3")'  # noqa: E501
        ],
        "warnings": [],
        "notices": [
            'Route does not have a return direction (relation 155, "02: 1-2-3")',  # noqa: E501
            'Route does not have a return direction (relation 158, "02: 1-3 (2)")',  # noqa: E501
            'Only one route in route_master. Please check if it needs a return route (relation 159, "C: 1-3-5-1")',  # noqa: E501
            'Route does not have a return direction (relation 163, "04: 1-2-3")',  # noqa: E501
            'Route does not have a return direction (relation 164, "04: 2-1")',  # noqa: E501
            'Stop Station 2 (1.0, 0.0) is included in the r203 but not included in r204 (relation 204, "2: 3-1")',  # noqa: E501
            'Route does not have a return direction (relation 205, "3: 1-2-3")',  # noqa: E501
            'Route does not have a return direction (relation 206, "3: 1-2-3")',  # noqa: E501
            'Route does not have a return direction (relation 207, "4: 4-3-2-1")',  # noqa: E501
            'Route does not have a return direction (relation 208, "4: 1-2-3-4")',  # noqa: E501
            'Route does not have a return direction (relation 209, "5: 1-2-3")',  # noqa: E501
            'Route does not have a return direction (relation 210, "5: 2-1")',  # noqa: E501
            'Only one route in route_master. Please check if it needs a return route (relation 213, "C3: 1-2-3-8-1")',  # noqa: E501
            'Route does not have a return direction (relation 168, "C5: 1-3-5-1")',  # noqa: E501
            'Route does not have a return direction (relation 169, "C5: 3-5-1-3")',  # noqa: E501
        ],
    },
]
