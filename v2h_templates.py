# These are templates for validation_to_html.py
# Variables should be in curly braces

STYLE = '''
<style>
body {
  font-family: sans-serif;
  font-size: 12pt;
  margin: 0px;
}
main {
  margin: 10px;
}
main {
  margin: 0 auto;
  max-width: 900px;
}
th {
  font-size: 10pt;
}
.errors {
  font-size: 10pt;
  color: #ED0000;
}
.warnings {
  font-size: 10pt;
  color: saddlebrown;
}
.notices {
  font-size: 10pt;
  color: darkblue;
}
.bold {
  font-weight: bold;
}
.color0 {
  background: pink;
}
.color1 {
  background: lightgreen;
}
.hlink {
  color: #888;
  opacity: 0.5;
}
table {
    max-width: 900px;
}
tr:hover td:nth-child(n+2) {
    filter: hue-rotate(-50deg);
}
td {
  border-radius: 2px;
}
td > div {
    margin-bottom: 0.8em;
}
.tooltip {
    font-weight: bold;
    position: relative;
    text-align: left;
}
.tooltip div {
    display: inline-block;
    width: 19px;
}
.tooltip:before {
    content: attr(data-text);
    position: absolute;
    top: 100%;
    left: 0;
    margin-top: 14px;
    width: 200px;
    padding: 10px;
    border-radius: 10px;
    background: lightblue;
    color: black;
    text-align: center;
    opacity: 0;
    transition: .3s opacity;
    visibility: hidden;
    z-index: 10
}
.tooltip:after {
    content: "";
    position: absolute;
    margin-top: -5px;
    top: 100%;
    left: 30px;
    border: 10px solid #000;
    border-color: transparent transparent lightblue transparent;
    visibility: hidden;
    opacity: 0;
    transition: .3s opacity
}
.tooltip:hover {
    text-decoration: none
}
.tooltip:hover:before,.tooltip:hover:after {
    opacity: 1;
    visibility: visible 
}
footer {
    background: white;
    border-top: 1px solid grey;
    bottom: 0px;
    padding: 10px;
    position: sticky;
}
</style>
'''

INDEX_HEADER = '''
<!doctype html>
<html>
<head>
<title>Subway Validator</title>
<meta charset="utf-8">
(s)
</head>
<body>
<main>
<h1>Subway Validation Results</h1>
<p><b>{good_cities}</b> of <b>{total_cities}</b> networks validated without errors.
To make a network validate successfully please follow the
<a href="https://wiki.openstreetmap.org/wiki/Metro_Mapping">metro mapping instructions</a>.
Commit your changes to the OSM and then check back to the updated validation results after the next validation cycle, please.
See <a href="https://wiki.openstreetmap.org/wiki/Quality_assurance#subway-preprocessor">the validator instance&#0040;s&#0041; description</a>
for the schedule and capabilities.</p>
<p><a href="render.html">View networks on a map</a></p>
<table cellspacing="3" cellpadding="2" style="margin-bottom: 1em;">
'''.replace('(s)', STYLE)

INDEX_CONTINENT = '''
<tr><td colspan="9">&nbsp;</td></tr>
<tr>
<th>Continent</th>
<th>Country</th>
<th>Good Cities</th>
<th>Subway Lines</th>
<th>Light Rail Lines</th>
<th>Stations</th>
<th>Interchanges</th>
<th>Errors</th>
<th>Warnings</th>
<th>Notices</th>
</tr>
<tr>
<td colspan="2" class="bold color{=cities}">{continent}</td>
<td class="color{=cities}">{good_cities} / {total_cities}</td>
<td class="color{=subwayl}">{subwayl_found} / {subwayl_expected}</td>
<td class="color{=lightrl}">{lightrl_found} / {lightrl_expected}</td>
<td class="color{=stations}">{stations_found} / {stations_expected}</td>
<td class="color{=transfers}">{transfers_found} / {transfers_expected}</td>
<td class="color{=errors}">{num_errors}</td>
<td class="color{=warnings}">{num_warnings}</td>
<td class="color{=notices}">{num_notices}</td>
</tr>
{content}
'''

INDEX_COUNTRY = '''
<tr>
<td>&nbsp;</td>
<td class="bold color{=cities}"><a href="{file}">{country}</a></td>
<td class="color{=cities}">{good_cities} / {total_cities}</td>
<td class="color{=subwayl}">{subwayl_found} / {subwayl_expected}</td>
<td class="color{=lightrl}">{lightrl_found} / {lightrl_expected}</td>
<td class="color{=stations}">{stations_found} / {stations_expected}</td>
<td class="color{=transfers}">{transfers_found} / {transfers_expected}</td>
<td class="color{=errors}">{num_errors}</td>
<td class="color{=warnings}">{num_warnings}</td>
<td class="color{=notices}">{num_notices}</td>
</tr>
'''

INDEX_FOOTER = '''
</table>
</main>
<footer>Produced by <a href="https://github.com/alexey-zakharenkov/subways">Subway Preprocessor</a> on {date}.
See <a href="{google}">this spreadsheet</a> for the reference metro statistics and
<a href="https://en.wikipedia.org/wiki/List_of_metro_systems#List">this wiki page</a> for a list
of all metro systems.</footer>
</body>
</html>
'''

COUNTRY_HEADER = '''
<!doctype html>
<html>
<head>
<title>Subway Validator: {country}</title>
<meta charset="utf-8">
(s)
</head>
<body>
<main>
<h1>Subway Validation Results for {country}</h1>
<p><a href="index.html">Return to the countries list</a>.</p>
<table cellspacing="3" cellpadding="2">
<tr>
<th>City</th>
{?subways}
<th>Subway Lines</th>
<th>Light Rail Lines</th>
{end}{?overground}
<th>Tram Lines</th>
<th>Bus Lines</th>
<th>T-Bus Lines</th>
<th>Other Lines</th>
{end}
<th>Stations</th>
<th>Interchanges</th>
<th>Unused Entrances</th>
</tr>
'''.replace('(s)', STYLE)

COUNTRY_CITY = '''
<tr id="{slug}">
<td class="bold color{good_cities}">
  {city}
  {?yaml}<a href="{yaml}" class="hlink" title="Download YAML">Y</a>{end}
  {?json}<a href="{json}" class="hlink" title="Download GeoJSON">J</a>{end}
  {?json}<a href="render.html#{slug}" class="hlink" title="View map" target="_blank">M</a>{end}
</td>
{?subways}
<td class="color{=subwayl}">sub: {subwayl_found} / {subwayl_expected}</td>
<td class="color{=lightrl}">lr: {lightrl_found} / {lightrl_expected}</td>
{end}{?overground}
<td class="color{=traml}">t: {traml_found} / {traml_expected}</td>
<td class="color{=busl}">b: {busl_found} / {busl_expected}</td>
<td class="color{=trolleybusl}">tb: {trolleybusl_found} / {trolleybusl_expected}</td>
<td class="color{=otherl}">o: {otherl_found} / {otherl_expected}</td>
{end}
<td class="color{=stations}">st: {stations_found} / {stations_expected}</td>
<td class="color{=transfers}">int: {transfers_found} / {transfers_expected}</td>
<td class="color{=entrances}">ent: {unused_entrances}</td>
</tr>
<tr><td colspan="{?subways}6{end}{?overground}8{end}">
{?errors}
<div class="errors"><div data-text="Network is invalid and not suitable for routing." class="tooltip">🛑 Errors</div>
{errors}
</div>
{end}
{?warnings}
<div class="warnings"><div data-text="Problematic data but it's still possible to build routes." class="tooltip">⚠️ Warnings</div>
{warnings}
</div>
{end}
{?notices}
<div class="notices"><div data-text="Suspicious condition but not necessarily an error." class="tooltip">ℹ️ Notices</div>
{notices}
{end}
</div>
</td></tr>
'''

COUNTRY_FOOTER = '''
</table>
</main>
<footer>Produced by <a href="https://github.com/alexey-zakharenkov/subways">Subway Preprocessor</a> on {date}.</footer>
</body>
</html>
'''
