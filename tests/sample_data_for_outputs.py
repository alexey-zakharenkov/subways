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
        "gtfs_file": "assets/tiny_world_gtfs.zip",
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
      "entrances": []
    },
    "n4": {
      "id": "n4",
      "center": [
        0,
        0.01
      ],
      "name": "Station 4",
      "entrances": []
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
      "entrances": []
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
    },
]
