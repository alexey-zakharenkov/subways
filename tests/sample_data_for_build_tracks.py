sample_networks = {
    "Only 2 stations, no rails": {
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
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "num_stations": 2,
        "tracks": [],
        "extended_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
        ],
        "truncated_tracks": [],
        "forward": {
            "first_stop_on_rails_index": 2,
            "last_stop_on_rails_index": 1,
            "positions_on_rails": [],
        },
        "backward": {
            "first_stop_on_rails_index": 2,
            "last_stop_on_rails_index": 1,
            "positions_on_rails": [],
        },
    },
    "Only 2 stations connected with rails": {
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
  <way id='1' version='1'>
    <nd ref='1' />
    <nd ref='2' />
    <tag k='railway' v='subway' />
  </way>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
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
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "num_stations": 2,
        "tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
        ],
        "extended_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
        ],
        "truncated_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
        ],
        "forward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 1,
            "positions_on_rails": [[0], [1]],
        },
        "backward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 1,
            "positions_on_rails": [[0], [1]],
        },
    },
    "Only 6 stations, no rails": {
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
  <node id='5' version='1' lat='0.0' lon='4.0'>
    <tag k='name' v='Station 5' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='6' version='1' lat='0.0' lon='5.0'>
    <tag k='name' v='Station 6' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='6' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='6' role='' />
    <member type='node' ref='5' role='' />
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
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "num_stations": 6,
        "tracks": [],
        "extended_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "truncated_tracks": [],
        "forward": {
            "first_stop_on_rails_index": 6,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [],
        },
        "backward": {
            "first_stop_on_rails_index": 6,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [],
        },
    },
    "One rail line connecting all stations": {
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
  <node id='5' version='1' lat='0.0' lon='4.0'>
    <tag k='name' v='Station 5' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='6' version='1' lat='0.0' lon='5.0'>
    <tag k='name' v='Station 6' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <way id='1' version='1'>
    <nd ref='1' />
    <nd ref='2' />
    <nd ref='3' />
    <nd ref='4' />
    <nd ref='5' />
    <nd ref='6' />
    <tag k='railway' v='subway' />
  </way>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='6' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='6' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='4' role='' />
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
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "num_stations": 6,
        "tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "extended_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "truncated_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "forward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [[0], [1], [2], [3], [4], [5]],
        },
        "backward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [[0], [1], [2], [3], [4], [5]],
        },
    },
    "One rail line connecting all stations except the last": {
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
  <node id='5' version='1' lat='0.0' lon='4.0'>
    <tag k='name' v='Station 5' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='6' version='1' lat='0.0' lon='5.0'>
    <tag k='name' v='Station 6' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <way id='1' version='1'>
    <nd ref='1' />
    <nd ref='2' />
    <nd ref='3' />
    <nd ref='4' />
    <nd ref='5' />
    <tag k='railway' v='subway' />
  </way>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='6' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='6' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='4' role='' />
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
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "num_stations": 6,
        "tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
        ],
        "extended_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "truncated_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
        ],
        "forward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 4,
            "positions_on_rails": [[0], [1], [2], [3], [4]],
        },
        "backward": {
            "first_stop_on_rails_index": 1,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [[0], [1], [2], [3], [4]],
        },
    },
    "One rail line connecting all stations except the fist": {
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
  <node id='5' version='1' lat='0.0' lon='4.0'>
    <tag k='name' v='Station 5' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='6' version='1' lat='0.0' lon='5.0'>
    <tag k='name' v='Station 6' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <way id='1' version='1'>
    <nd ref='2' />
    <nd ref='3' />
    <nd ref='4' />
    <nd ref='5' />
    <nd ref='6' />
    <tag k='railway' v='subway' />
  </way>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='6' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='6' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='4' role='' />
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
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "num_stations": 6,
        "tracks": [
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "extended_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "truncated_tracks": [
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "forward": {
            "first_stop_on_rails_index": 1,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [[0], [1], [2], [3], [4]],
        },
        "backward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 4,
            "positions_on_rails": [[0], [1], [2], [3], [4]],
        },
    },
    "One rail line connecting all stations except the fist and the last": {
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
  <node id='5' version='1' lat='0.0' lon='4.0'>
    <tag k='name' v='Station 5' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='6' version='1' lat='0.0' lon='5.0'>
    <tag k='name' v='Station 6' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <way id='1' version='1'>
    <nd ref='2' />
    <nd ref='3' />
    <nd ref='4' />
    <nd ref='5' />
    <tag k='railway' v='subway' />
  </way>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='6' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='6' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='4' role='' />
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
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "num_stations": 6,
        "tracks": [
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
        ],
        "extended_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "truncated_tracks": [
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
        ],
        "forward": {
            "first_stop_on_rails_index": 1,
            "last_stop_on_rails_index": 4,
            "positions_on_rails": [[0], [1], [2], [3]],
        },
        "backward": {
            "first_stop_on_rails_index": 1,
            "last_stop_on_rails_index": 4,
            "positions_on_rails": [[0], [1], [2], [3]],
        },
    },
    "One rail line connecting only 2 first stations": {
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
  <node id='5' version='1' lat='0.0' lon='4.0'>
    <tag k='name' v='Station 5' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='6' version='1' lat='0.0' lon='5.0'>
    <tag k='name' v='Station 6' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <way id='1' version='1'>
    <nd ref='1' />
    <nd ref='2' />
    <tag k='railway' v='subway' />
  </way>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='6' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='6' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='4' role='' />
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
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "num_stations": 6,
        "tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
        ],
        "extended_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "truncated_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
        ],
        "forward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 1,
            "positions_on_rails": [[0], [1]],
        },
        "backward": {
            "first_stop_on_rails_index": 4,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [[0], [1]],
        },
    },
    "One rail line connecting only 2 last stations": {
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
  <node id='5' version='1' lat='0.0' lon='4.0'>
    <tag k='name' v='Station 5' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='6' version='1' lat='0.0' lon='5.0'>
    <tag k='name' v='Station 6' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <way id='1' version='1'>
    <nd ref='5' />
    <nd ref='6' />
    <tag k='railway' v='subway' />
  </way>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='6' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='6' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='4' role='' />
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
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "num_stations": 6,
        "tracks": [
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "extended_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "truncated_tracks": [
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "forward": {
            "first_stop_on_rails_index": 4,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [[0], [1]],
        },
        "backward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 1,
            "positions_on_rails": [[0], [1]],
        },
    },
    "One rail connecting all stations and protruding at both ends": {
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
  <node id='5' version='1' lat='0.0' lon='4.0'>
    <tag k='name' v='Station 5' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='6' version='1' lat='0.0' lon='5.0'>
    <tag k='name' v='Station 6' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='11' version='1' lat='0.0' lon='-1.0'>
  </node>
  <node id='12' version='1' lat='0.0' lon='6.0'>
  </node>
  <way id='1' version='1'>
    <nd ref='11' />
    <nd ref='1' />
    <nd ref='2' />
    <nd ref='3' />
    <nd ref='4' />
    <nd ref='5' />
    <nd ref='6' />
    <nd ref='12' />
    <tag k='railway' v='subway' />
  </way>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='6' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='6' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='4' role='' />
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
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "num_stations": 6,
        "tracks": [
            (-1.0, 0.0),
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
            (6.0, 0.0),
        ],
        "extended_tracks": [
            (-1.0, 0.0),
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
            (6.0, 0.0),
        ],
        "truncated_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "forward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [[1], [2], [3], [4], [5], [6]],
        },
        "backward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [[1], [2], [3], [4], [5], [6]],
        },
    },
    (
        "Several rails with reversed order for backward route, "
        "connecting all stations and protruding at both ends"
    ): {
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
  <node id='5' version='1' lat='0.0' lon='4.0'>
    <tag k='name' v='Station 5' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='6' version='1' lat='0.0' lon='5.0'>
    <tag k='name' v='Station 6' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='11' version='1' lat='0.0' lon='-1.0'>
  </node>
  <node id='12' version='1' lat='0.0' lon='6.0'>
  </node>
  <way id='1' version='1'>
    <nd ref='2' />
    <nd ref='1' />
    <nd ref='11' />
    <tag k='railway' v='subway' />
  </way>
  <way id='2' version='1' >
    <nd ref='2' />
    <nd ref='3' />
    <nd ref='4' />
    <nd ref='5' />
    <nd ref='6' />
    <nd ref='12' />
    <tag k='railway' v='subway' />
  </way>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='6' role='' />
    <member type='way' ref='1' role='' />
    <member type='way' ref='2' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='6' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='1' role='' />
    <member type='way' ref='1' role='' />
    <member type='way' ref='2' role='' />
    <tag k='name' v='Backward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='3' version='1'>
    <member type='relation' ref='1' role='' />
    <member type='relation' ref='2' role='' />
    <tag k='ref' v='1' />
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "num_stations": 6,
        "tracks": [
            (-1.0, 0.0),
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
            (6.0, 0.0),
        ],
        "extended_tracks": [
            (-1.0, 0.0),
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
            (6.0, 0.0),
        ],
        "truncated_tracks": [
            (0.0, 0.0),
            (1.0, 0.0),
            (2.0, 0.0),
            (3.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0),
        ],
        "forward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [[1], [2], [3], [4], [5], [6]],
        },
        "backward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [[1], [2], [3], [4], [5], [6]],
        },
    },
    (
        "One rail laying near all stations requiring station projecting, "
        "protruding at both ends"
    ): {
        "xml": """<?xml version='1.0' encoding='UTF-8'?>
<osm version='0.6' generator='JOSM'>
  <node id='1' version='1' lat='0.0001' lon='0.0'>
    <tag k='name' v='Station 1' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='2' version='1' lat='0.0001' lon='1.0'>
    <tag k='name' v='Station 2' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='3' version='1' lat='0.0001' lon='2.0'>
    <tag k='name' v='Station 3' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='4' version='1' lat='0.0001' lon='3.0'>
    <tag k='name' v='Station 4' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='5' version='1' lat='0.0001' lon='4.0'>
    <tag k='name' v='Station 5' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='6' version='1' lat='0.0001' lon='5.0'>
    <tag k='name' v='Station 6' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='11' version='1' lat='0.0' lon='-1.0'>
  </node>
  <node id='12' version='1' lat='0.0' lon='6.0'>
  </node>
  <way id='1' version='1'>
    <nd ref='11' />
    <nd ref='12' />
    <tag k='railway' v='subway' />
  </way>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='6' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='6' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='4' role='' />
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
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "num_stations": 6,
        "tracks": [
            (-1.0, 0.0),
            (6.0, 0.0),
        ],
        "extended_tracks": [
            (-1.0, 0.0),
            (6.0, 0.0),
        ],
        "truncated_tracks": [
            (0.0, 0.0),
            (5.0, 0.0),
        ],
        "forward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [
                [1 / 7],
                [2 / 7],
                [3 / 7],
                [4 / 7],
                [5 / 7],
                [6 / 7],
            ],
        },
        "backward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 5,
            "positions_on_rails": [
                [1 / 7],
                [2 / 7],
                [3 / 7],
                [4 / 7],
                [5 / 7],
                [6 / 7],
            ],
        },
    },
    "One rail laying near all stations except the first and last": {
        "xml": """<?xml version='1.0' encoding='UTF-8'?>
<osm version='0.6' generator='JOSM'>
  <node id='1' version='1' lat='0.0001' lon='0.0'>
    <tag k='name' v='Station 1' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='2' version='1' lat='0.0001' lon='1.0'>
    <tag k='name' v='Station 2' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='3' version='1' lat='0.0001' lon='2.0'>
    <tag k='name' v='Station 3' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='4' version='1' lat='0.0001' lon='3.0'>
    <tag k='name' v='Station 4' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='5' version='1' lat='0.0001' lon='4.0'>
    <tag k='name' v='Station 5' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='6' version='1' lat='0.0001' lon='5.0'>
    <tag k='name' v='Station 6' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='11' version='1' lat='0.0' lon='1.0'>
  </node>
  <node id='12' version='1' lat='0.0' lon='4.0'>
  </node>
  <way id='1' version='1'>
    <nd ref='11' />
    <nd ref='12' />
    <tag k='railway' v='subway' />
  </way>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='6' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='6' role='' />
    <member type='node' ref='5' role='' />
    <member type='node' ref='4' role='' />
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
    <tag k='route_master' v='subway' />
    <tag k='type' v='route_master' />
  </relation>
</osm>
""",
        "num_stations": 6,
        "tracks": [
            (1.0, 0.0),
            (4.0, 0.0),
        ],
        "extended_tracks": [
            (0.0, 0.0001),
            (1.0, 0.0),
            (4.0, 0.0),
            (5.0, 0.0001),
        ],
        "truncated_tracks": [
            (1.0, 0.0),
            (4.0, 0.0),
        ],
        "forward": {
            "first_stop_on_rails_index": 1,
            "last_stop_on_rails_index": 4,
            "positions_on_rails": [[0], [1 / 3], [2 / 3], [1]],
        },
        "backward": {
            "first_stop_on_rails_index": 1,
            "last_stop_on_rails_index": 4,
            "positions_on_rails": [[0], [1 / 3], [2 / 3], [1]],
        },
    },
    "Circle route without rails": {
        "xml": """<?xml version='1.0' encoding='UTF-8'?>
<osm version='0.6' generator='JOSM'>
  <node id='1' version='1' lat='0.0' lon='0.0'>
    <tag k='name' v='Station 1' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='2' version='1' lat='1.0' lon='0.0'>
    <tag k='name' v='Station 2' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='3' version='1' lat='1.0' lon='1.0'>
    <tag k='name' v='Station 3' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='4' version='1' lat='0.0' lon='1.0'>
    <tag k='name' v='Station 4' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='1' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='1' role='' />
    <tag k='name' v='Backward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
</osm>
""",
        "num_stations": 4,
        "tracks": [],
        "extended_tracks": [
            (0.0, 0.0),
            (0.0, 1.0),
            (1.0, 1.0),
            (1.0, 0.0),
            (0.0, 0.0),
        ],
        "truncated_tracks": [],
        "forward": {
            "first_stop_on_rails_index": 5,
            "last_stop_on_rails_index": 4,
            "positions_on_rails": [],
        },
        "backward": {
            "first_stop_on_rails_index": 5,
            "last_stop_on_rails_index": 4,
            "positions_on_rails": [],
        },
    },
    "Circle route with closed rail line connecting all stations": {
        "xml": """<?xml version='1.0' encoding='UTF-8'?>
<osm version='0.6' generator='JOSM'>
  <node id='1' version='1' lat='0.0' lon='0.0'>
    <tag k='name' v='Station 1' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='2' version='1' lat='1.0' lon='0.0'>
    <tag k='name' v='Station 2' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='3' version='1' lat='1.0' lon='1.0'>
    <tag k='name' v='Station 3' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <node id='4' version='1' lat='0.0' lon='1.0'>
    <tag k='name' v='Station 4' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <way id='1' version='1'>
    <nd ref='1' />
    <nd ref='2' />
    <nd ref='3' />
    <nd ref='4' />
    <nd ref='1' />
    <tag k='railway' v='subway' />
  </way>
  <relation id='1' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='1' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Forward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
  <relation id='2' version='1'>
    <member type='node' ref='1' role='' />
    <member type='node' ref='4' role='' />
    <member type='node' ref='3' role='' />
    <member type='node' ref='2' role='' />
    <member type='node' ref='1' role='' />
    <member type='way' ref='1' role='' />
    <tag k='name' v='Backward' />
    <tag k='ref' v='1' />
    <tag k='route' v='subway' />
    <tag k='type' v='route' />
  </relation>
</osm>
""",
        "num_stations": 4,
        "tracks": [
            (0.0, 0.0),
            (0.0, 1.0),
            (1.0, 1.0),
            (1.0, 0.0),
            (0.0, 0.0),
        ],
        "extended_tracks": [
            (0.0, 0.0),
            (0.0, 1.0),
            (1.0, 1.0),
            (1.0, 0.0),
            (0.0, 0.0),
        ],
        "truncated_tracks": [
            (0.0, 0.0),
            (0.0, 1.0),
            (1.0, 1.0),
            (1.0, 0.0),
            (0.0, 0.0),
        ],
        "forward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 4,
            "positions_on_rails": [[0, 4], [1], [2], [3], [0, 4]],
        },
        "backward": {
            "first_stop_on_rails_index": 0,
            "last_stop_on_rails_index": 4,
            "positions_on_rails": [[0, 4], [1], [2], [3], [0, 4]],
        },
    },
}
