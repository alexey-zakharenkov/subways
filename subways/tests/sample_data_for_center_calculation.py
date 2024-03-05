metro_samples = [
    {
        "name": "Transfer at Kuntsevskaya",
        "xml": """<?xml version='1.0' encoding='UTF-8'?>
<osm version='0.6' generator='JOSM'>
  <node id='244036218' visible='true' version='27' lat='55.7306986' lon='37.4460134'>
    <tag k='public_transport' v='stop_position' />
    <tag k='subway' v='yes' />
  </node>
  <node id='244038961' visible='true' version='26' lat='55.730801' lon='37.4464724'>
    <tag k='railway' v='subway_entrance' />
  </node>
  <node id='461075776' visible='true' version='5' lat='55.7304682' lon='37.4447392' />
  <node id='461075811' visible='true' version='7' lat='55.7308273' lon='37.4473927'>
    <tag k='barrier' v='gate' />
  </node>
  <node id='1191237441' visible='true' version='18' lat='55.7308185' lon='37.4459574'>
    <tag k='public_transport' v='stop_position' />
    <tag k='subway' v='yes' />
  </node>
  <node id='4821481210' visible='true' version='3' lat='55.7305372' lon='37.4447339' />
  <node id='4821481211' visible='true' version='3' lat='55.7306293' lon='37.4446944' />
  <node id='4821481212' visible='true' version='3' lat='55.7308921' lon='37.4473467' />
  <node id='4821481213' visible='true' version='3' lat='55.7309843' lon='37.4473072' />
  <node id='5176248500' visible='true' version='2' lat='55.7306626' lon='37.4460524'>
    <tag k='public_transport' v='stop_position' />
    <tag k='subway' v='yes' />
  </node>
  <node id='5176248502' visible='true' version='8' lat='55.7306808' lon='37.4460281'>
    <tag k='name' v='Кунцевская' />
    <tag k='railway' v='station' />
    <tag k='station' v='subway' />
  </node>
  <way id='38836456' version='4' visible='true'>
    <nd ref='461075776' />
    <nd ref='461075811' />
    <tag k='railway' v='platform' />
  </way>
  <way id='489951237' visible='true' version='6'>
    <nd ref='4821481210' />
    <nd ref='4821481211' />
    <nd ref='4821481213' />
    <nd ref='4821481212' />
    <nd ref='4821481210' />
  </way>
  <relation id='7588527' visible='true' version='7'>
    <member type='node' ref='5176248502' role='' />
    <member type='node' ref='5176248500' role='stop' />
    <member type='way' ref='38836456' role='' />
    <tag k='public_transport' v='stop_area' />
    <tag k='type' v='public_transport' />
  </relation>
  <relation id='7588528' visible='true' version='6'>
    <member type='node' ref='5176248502' role='' />
    <member type='node' ref='244036218' role='stop' />
    <member type='node' ref='1191237441' role='stop' />
    <member type='relation' ref='13426423' role='platform' />
    <member type='node' ref='244038961' role='' />
    <member type='relation' ref='7588561' role='' /> <!-- cyclic ref -->
    <tag k='public_transport' v='stop_area' />
    <tag k='type' v='public_transport' />
  </relation>
  <relation id='7588561' visible='true' version='5'>
    <member type='relation' ref='7588528' role='' />
    <member type='relation' ref='7588527' role='' />
    <member type='node' ref='1' role='' /> <!-- incomplete ref -->
    <member type='way' ref='1' role='' /> <!-- incomplete ref -->
    <member type='relation' ref='1' role='' /> <!-- incomplete ref -->
    <tag k='name' v='Кунцевская' />
    <tag k='public_transport' v='stop_area_group' />
    <tag k='type' v='public_transport' />
  </relation>
  <relation id='13426423' visible='true' version='4'>
    <member type='way' ref='489951237' role='outer' />
    <tag k='public_transport' v='platform' />
    <tag k='type' v='multipolygon' />
  </relation>
  <relation id='100' visible='true' version='1'>
    <tag k='description' v='emtpy relation' />
  </relation>
  <relation id='101' visible='true' version='1'>
    <member type='node' ref='1' role='' /> <!-- incomplete ref -->
    <tag k='description' v='only incomplete members' />
  </relation>
</osm>
""",  # noqa: E501
        "expected_centers": {
            "w38836456": {"lat": 55.73064775, "lon": 37.446065950000005},
            "w489951237": {"lat": 55.730760724999996, "lon": 37.44602055},
            "r7588527": {"lat": 55.73066371666667, "lon": 37.44604881666667},
            "r7588528": {"lat": 55.73075192499999, "lon": 37.44609837},
            "r7588561": {"lat": 55.73070782083333, "lon": 37.44607359333334},
            "r13426423": {"lat": 55.730760724999996, "lon": 37.44602055},
            "r100": None,
            "r101": None,
        },
    },
]
