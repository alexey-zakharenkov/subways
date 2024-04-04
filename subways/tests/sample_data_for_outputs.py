metro_samples = [
    {
        "name": "tiny_world",
        "xml_file": """assets/tiny_world.osm""",
        "cities_info": [
            {
                "id": 1,
                "name": "Intersecting 2 metro lines",
                "num_stations": 4 + 2,
                "num_lines": 2,
                "num_interchanges": 1,
                "networks": "network-1",
            },
            {
                "id": 2,
                "name": "One light rail line",
                "num_stations": 2,
                "num_lines": 0,
                "num_light_lines": 1,
                "networks": "network-2",
            },
        ],
        "gtfs_dir": "assets/tiny_world_gtfs",
        "transfers": [{"r1", "r2"}, {"r3", "r4"}],
        "json_dump": """
{
  "stopareas": {
    "n1": {
      "id": "n1",
      "center": [
        0,
        0
      ],
      "name": "Station 1",
      "entrances": []
    },
    "r1": {
      "id": "r1",
      "center": [
        0.00470373068,
        0.0047037307
      ],
      "name": "Station 2",
      "entrances": []
    },
    "r3": {
      "id": "r3",
      "center": [
        0.01012040581,
        0.0097589171
      ],
      "name": "Station 3",
      "entrances": [
        {
          "id": "n201",
          "name": null,
          "ref": "3-1",
          "center": [0.01007169217, 0.00967473055]
        },
        {
          "id": "n202",
          "name": null,
          "ref": "3-2",
          "center": [0.01018702716, 0.00966936613]
        }
      ]
    },
    "n4": {
      "id": "n4",
      "center": [
        0,
        0.01
      ],
      "name": "Station 4",
      "entrances": [
        {
          "id": "n205",
          "name": null,
          "ref": "4-1",
          "center": [0.000201163, 0.01015484596]
        }
      ]
    },
    "r2": {
      "id": "r2",
      "center": [
        0.0047718624,
        0.00514739839
      ],
      "name": "Station 5",
      "entrances": []
    },
    "n6": {
      "id": "n6",
      "center": [
        0.01,
        0
      ],
      "name": "Station 6",
      "entrances": []
    },
    "r4": {
      "id": "r4",
      "center": [
        0.009716854315,
        0.010286367745
      ],
      "name": "Station 7",
      "entrances": [
        {
          "id": "n204",
          "name": null,
          "ref": "7-1",
          "center": [0.00952183932, 0.01034796501]
        },
        {
          "id": "n203",
          "name": null,
          "ref": "7-2",
          "center": [0.00959962338, 0.01042574907]
        }
      ]
    },
    "r16": {
      "id": "r16",
      "center": [
        0.012405493905,
        0.014377764559999999
      ],
      "name": "Station 8",
      "entrances": []
    }
  },
  "networks": {
    "Intersecting 2 metro lines": {
      "id": 1,
      "name": "Intersecting 2 metro lines",
      "routes": [
        {
          "id": "r15",
          "mode": "subway",
          "ref": "1",
          "name": "Blue Line",
          "colour": "#0000ff",
          "infill": null,
          "itineraries": [
            {
              "id": "r7",
              "tracks": [
                [
                  0,
                  0
                ],
                [
                  0.00470373068,
                  0.0047037307
                ],
                [
                  0.009939661455227341,
                  0.009939661455455193
                ]
              ],
              "start_time": null,
              "end_time": null,
              "interval": null,
              "duration": null,
              "stops": [
                {
                  "stoparea_id": "n1",
                  "distance": 0
                },
                {
                  "stoparea_id": "r1",
                  "distance": 741
                },
                {
                  "stoparea_id": "r3",
                  "distance": 1565
                }
              ]
            },
            {
              "id": "r8",
              "tracks": [
                [
                  0.009939661455227341,
                  0.009939661455455193
                ],
                [
                  0.00470373068,
                  0.0047037307
                ],
                [
                  0,
                  0
                ]
              ],
              "start_time": null,
              "end_time": null,
              "interval": null,
              "duration": null,
              "stops": [
                {
                  "stoparea_id": "r3",
                  "distance": 0
                },
                {
                  "stoparea_id": "r1",
                  "distance": 824
                },
                {
                  "stoparea_id": "n1",
                  "distance": 1565
                }
              ]
            }
          ]
        },
        {
          "id": "r14",
          "mode": "subway",
          "ref": "2",
          "name": "Red Line",
          "colour": "#ff0000",
          "infill": null,
          "itineraries": [
            {
              "id": "r12",
              "tracks": [
                [
                  0,
                  0.01
                ],
                [
                  0.01,
                  0
                ]
              ],
              "start_time": null,
              "end_time": null,
              "interval": null,
              "duration": 600,
              "stops": [
                {
                  "stoparea_id": "n4",
                  "distance": 0
                },
                {
                  "stoparea_id": "r2",
                  "distance": 758
                },
                {
                  "stoparea_id": "n6",
                  "distance": 1575
                }
              ]
            },
            {
              "id": "r13",
              "tracks": [
                [
                  0.01,
                  0
                ],
                [
                  0,
                  0.01
                ]
              ],
              "start_time": null,
              "end_time": null,
              "interval": null,
              "duration": 480,
              "stops": [
                {
                  "stoparea_id": "n6",
                  "distance": 0
                },
                {
                  "stoparea_id": "r2",
                  "distance": 817
                },
                {
                  "stoparea_id": "n4",
                  "distance": 1575
                }
              ]
            }
          ]
        }
      ]
    },
    "One light rail line": {
      "id": 2,
      "name": "One light rail line",
      "routes": [
        {
          "id": "r11",
          "mode": "light_rail",
          "ref": "LR",
          "name": "LR Line",
          "colour": "#a52a2a",
          "infill": "#ffffff",
          "itineraries": [
            {
              "id": "r9",
              "tracks": [
                [
                  0.00976752835,
                  0.01025306758
                ],
                [
                  0.01245616794,
                  0.01434446439
                ]
              ],
              "start_time": null,
              "end_time": null,
              "interval": null,
              "duration": 300,
              "stops": [
                {
                  "stoparea_id": "r4",
                  "distance": 0
                },
                {
                  "stoparea_id": "r16",
                  "distance": 545
                }
              ]
            },
            {
              "id": "r10",
              "tracks": [
                [
                  0.012321033122529725,
                  0.014359650255679167
                ],
                [
                  0.00966618028,
                  0.01031966791
                ]
              ],
              "start_time": null,
              "end_time": null,
              "interval": null,
              "duration": 300,
              "stops": [
                {
                  "stoparea_id": "r16",
                  "distance": 0
                },
                {
                  "stoparea_id": "r4",
                  "distance": 538
                }
              ]
            }
          ]
        }
      ]
    }
  },
  "transfers": [
    [
      "r1",
      "r2"
    ],
    [
      "r3",
      "r4"
    ]
  ]
}
""",
        "mapsme_output": {
            "stops": [
                {
                    "name": "Station 1",
                    "int_name": None,
                    "lat": 0.0,
                    "lon": 0.0,
                    "osm_type": "node",
                    "osm_id": 1,
                    "id": 8,
                    "entrances": [
                        {
                            "osm_type": "node",
                            "osm_id": 1,
                            "lon": 0.0,
                            "lat": 0.0,
                            "distance": 60,
                        }
                    ],
                    "exits": [
                        {
                            "osm_type": "node",
                            "osm_id": 1,
                            "lon": 0.0,
                            "lat": 0.0,
                            "distance": 60,
                        }
                    ],
                },
                {
                    "name": "Station 2",
                    "int_name": None,
                    "lat": 0.0047037307,
                    "lon": 0.00470373068,
                    "osm_type": "node",
                    "osm_id": 2,
                    "id": 14,
                    "entrances": [
                        {
                            "osm_type": "node",
                            "osm_id": 2,
                            "lon": 0.0047209447,
                            "lat": 0.004686516680000001,
                            "distance": 60,
                        }
                    ],
                    "exits": [
                        {
                            "osm_type": "node",
                            "osm_id": 2,
                            "lon": 0.0047209447,
                            "lat": 0.004686516680000001,
                            "distance": 60,
                        }
                    ],
                },
                {
                    "name": "Station 3",
                    "int_name": None,
                    "lat": 0.0097589171,
                    "lon": 0.01012040581,
                    "osm_type": "node",
                    "osm_id": 3,
                    "id": 30,
                    "entrances": [
                        {
                            "osm_type": "node",
                            "osm_id": 201,
                            "lon": 0.01007169217,
                            "lat": 0.00967473055,
                            "distance": 68,
                        },
                        {
                            "osm_type": "node",
                            "osm_id": 202,
                            "lon": 0.01018702716,
                            "lat": 0.00966936613,
                            "distance": 69,
                        },
                    ],
                    "exits": [
                        {
                            "osm_type": "node",
                            "osm_id": 201,
                            "lon": 0.01007169217,
                            "lat": 0.00967473055,
                            "distance": 68,
                        },
                        {
                            "osm_type": "node",
                            "osm_id": 202,
                            "lon": 0.01018702716,
                            "lat": 0.00966936613,
                            "distance": 69,
                        },
                    ],
                },
                {
                    "name": "Station 4",
                    "int_name": None,
                    "lat": 0.01,
                    "lon": 0.0,
                    "osm_type": "node",
                    "osm_id": 4,
                    "id": 32,
                    "entrances": [
                        {
                            "osm_type": "node",
                            "osm_id": 205,
                            "lon": 0.000201163,
                            "lat": 0.01015484596,
                            "distance": 80,
                        }
                    ],
                    "exits": [
                        {
                            "osm_type": "node",
                            "osm_id": 205,
                            "lon": 0.000201163,
                            "lat": 0.01015484596,
                            "distance": 80,
                        }
                    ],
                },
                {
                    "name": "Station 5",
                    "int_name": None,
                    "lat": 0.00514739839,
                    "lon": 0.0047718624,
                    "osm_type": "node",
                    "osm_id": 5,
                    "id": 22,
                    "entrances": [
                        {
                            "osm_type": "node",
                            "osm_id": 5,
                            "lon": 0.0047718624,
                            "lat": 0.00514739839,
                            "distance": 60,
                        }
                    ],
                    "exits": [
                        {
                            "osm_type": "node",
                            "osm_id": 5,
                            "lon": 0.0047718624,
                            "lat": 0.00514739839,
                            "distance": 60,
                        }
                    ],
                },
                {
                    "name": "Station 6",
                    "int_name": None,
                    "lat": 0.0,
                    "lon": 0.01,
                    "osm_type": "node",
                    "osm_id": 6,
                    "id": 48,
                    "entrances": [
                        {
                            "osm_type": "node",
                            "osm_id": 6,
                            "lon": 0.01,
                            "lat": 0.0,
                            "distance": 60,
                        }
                    ],
                    "exits": [
                        {
                            "osm_type": "node",
                            "osm_id": 6,
                            "lon": 0.01,
                            "lat": 0.0,
                            "distance": 60,
                        }
                    ],
                },
                {
                    "name": "Station 7",
                    "int_name": None,
                    "lat": 0.010286367745,
                    "lon": 0.009716854315,
                    "osm_type": "node",
                    "osm_id": 7,
                    "id": 38,
                    "entrances": [
                        {
                            "osm_type": "node",
                            "osm_id": 203,
                            "lon": 0.00959962338,
                            "lat": 0.01042574907,
                            "distance": 75,
                        },
                        {
                            "osm_type": "node",
                            "osm_id": 204,
                            "lon": 0.00952183932,
                            "lat": 0.01034796501,
                            "distance": 76,
                        },
                    ],
                    "exits": [
                        {
                            "osm_type": "node",
                            "osm_id": 203,
                            "lon": 0.00959962338,
                            "lat": 0.01042574907,
                            "distance": 75,
                        },
                        {
                            "osm_type": "node",
                            "osm_id": 204,
                            "lon": 0.00952183932,
                            "lat": 0.01034796501,
                            "distance": 76,
                        },
                    ],
                },
                {
                    "name": "Station 8",
                    "int_name": None,
                    "lat": 0.014377764559999999,
                    "lon": 0.012405493905,
                    "osm_type": "node",
                    "osm_id": 8,
                    "id": 134,
                    "entrances": [
                        {
                            "osm_type": "node",
                            "osm_id": 8,
                            "lon": 0.012391026016666667,
                            "lat": 0.01436273297,
                            "distance": 60,
                        }
                    ],
                    "exits": [
                        {
                            "osm_type": "node",
                            "osm_id": 8,
                            "lon": 0.012391026016666667,
                            "lat": 0.01436273297,
                            "distance": 60,
                        }
                    ],
                },
            ],
            "transfers": [(14, 22, 81), (30, 38, 106)],
            "networks": [
                {
                    "network": "Intersecting 2 metro lines",
                    "routes": [
                        {
                            "type": "subway",
                            "ref": "1",
                            "name": "Blue Line",
                            "colour": "0000ff",
                            "route_id": 30,
                            "itineraries": [
                                {
                                    "stops": [[8, 0], [14, 67], [30, 141]],
                                    "interval": 150,
                                },
                                {
                                    "stops": [[30, 0], [14, 74], [8, 141]],
                                    "interval": 150,
                                },
                            ],
                        },
                        {
                            "type": "subway",
                            "ref": "2",
                            "name": "Red Line",
                            "colour": "ff0000",
                            "route_id": 28,
                            "itineraries": [
                                {
                                    "stops": [[32, 0], [22, 68], [48, 142]],
                                    "interval": 150,
                                },
                                {
                                    "stops": [[48, 0], [22, 74], [32, 142]],
                                    "interval": 150,
                                },
                            ],
                        },
                    ],
                    "agency_id": 1,
                },
                {
                    "network": "One light rail line",
                    "routes": [
                        {
                            "type": "light_rail",
                            "ref": "LR",
                            "name": "LR Line",
                            "colour": "ffffff",
                            "route_id": 22,
                            "itineraries": [
                                {
                                    "stops": [[38, 0], [134, 49]],
                                    "interval": 150,
                                },
                                {
                                    "stops": [[134, 0], [38, 48]],
                                    "interval": 150,
                                },
                            ],
                            "casing": "a52a2a",
                        }
                    ],
                    "agency_id": 2,
                },
            ],
        },
    },
]
