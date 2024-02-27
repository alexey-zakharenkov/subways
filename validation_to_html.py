#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
from collections import defaultdict
from typing import Any

from process_subways import DEFAULT_SPREADSHEET_ID
from v2h_templates import (
    COUNTRY_CITY,
    COUNTRY_FOOTER,
    COUNTRY_HEADER,
    INDEX_CONTINENT,
    INDEX_COUNTRY,
    INDEX_FOOTER,
    INDEX_HEADER,
)


class CityData:
    def __init__(self, city: dict | None = None) -> None:
        self.data = {
            "good_cities": 0,
            "total_cities": 1 if city else 0,
            "num_errors": 0,
            "num_warnings": 0,
            "num_notices": 0,
        }
        self.slug = None
        if city:
            self.slug = city["slug"]
            self.country = city["country"]
            self.continent = city["continent"]
            self.errors = city["errors"]
            self.warnings = city["warnings"]
            self.notices = city["notices"]
            if not self.errors:
                self.data["good_cities"] = 1
            self.data["num_errors"] = len(self.errors)
            self.data["num_warnings"] = len(self.warnings)
            self.data["num_notices"] = len(self.notices)
            for k, v in city.items():
                if "found" in k or "expected" in k or "unused" in k:
                    self.data[k] = v

    def __add__(self, other: CityData) -> CityData:
        d = CityData()
        for k in set(self.data.keys()) | set(other.data.keys()):
            d.data[k] = self.data.get(k, 0) + other.data.get(k, 0)
        return d

    @staticmethod
    def test_eq(v1: Any, v2: Any) -> str:
        return "1" if v1 == v2 else "0"

    def format(self, s: str) -> str:
        for k in self.data:
            s = s.replace("{" + k + "}", str(self.data[k]))
        s = s.replace("{slug}", self.slug or "")
        for k in (
            "subwayl",
            "lightrl",
            "stations",
            "transfers",
            "busl",
            "trolleybusl",
            "traml",
            "otherl",
        ):
            if k + "_expected" in self.data:
                s = s.replace(
                    "{=" + k + "}",
                    self.test_eq(
                        self.data[k + "_found"], self.data[k + "_expected"]
                    ),
                )
        s = s.replace(
            "{=cities}",
            self.test_eq(self.data["good_cities"], self.data["total_cities"]),
        )
        s = s.replace(
            "{=entrances}", self.test_eq(self.data["unused_entrances"], 0)
        )
        for k in ("errors", "warnings", "notices"):
            s = s.replace(
                "{=" + k + "}", self.test_eq(self.data["num_" + k], 0)
            )
        return s


def tmpl(s: str, data: CityData | None = None, **kwargs) -> str:
    if data:
        s = data.format(s)
    if kwargs:
        for k, v in kwargs.items():
            if v is not None:
                s = s.replace("{" + k + "}", str(v))
            s = re.sub(
                r"\{\?" + k + r"\}(.+?)\{end\}",
                r"\1" if v else "",
                s,
                flags=re.DOTALL,
            )
    return s


EXPAND_OSM_TYPE = {"n": "node", "w": "way", "r": "relation"}
RE_SHORT = re.compile(r"\b([nwr])(\d+)\b")
RE_FULL = re.compile(r"\b(node|way|relation) (\d+)\b")
RE_COORDS = re.compile(r"\((-?\d+\.\d+), (-?\d+\.\d+)\)")


def osm_links(s: str) -> str:
    """Converts object mentions to HTML links."""

    def link(m: re.Match) -> str:
        osm_type = EXPAND_OSM_TYPE[m.group(1)[0]]
        osm_id = m.group(2)
        return (
            '<a href="https://www.openstreetmap.org/'
            f'{osm_type}/{osm_id}">{m.group(0)}</a>'
        )

    s = RE_SHORT.sub(link, s)
    s = RE_FULL.sub(link, s)
    s = RE_COORDS.sub(
        r'(<a href="https://www.openstreetmap.org/search?'
        r'query=\2%2C\1#map=18/\2/\1">pos</a>)',
        s,
    )
    return s


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def br_osm_links(elems: list) -> str:
    return "<br>".join(osm_links(esc(elem)) for elem in elems)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Reads a log from subway validator and prepares HTML files."
        )
    )
    parser.add_argument("validation_log")
    parser.add_argument("target_directory", nargs="?", default=".")
    parser.add_argument(
        "--cities-info-url",
        default=(
            "https://docs.google.com/spreadsheets/d/"
            f"{DEFAULT_SPREADSHEET_ID}/edit?usp=sharing"
        ),
    )
    options = parser.parse_args()
    target_dir = options.target_directory
    cities_info_url = options.cities_info_url

    with open(options.validation_log, encoding="utf-8") as f:
        data = {c["name"]: CityData(c) for c in json.load(f)}

    countries = {}
    continents = {}
    c_by_c = defaultdict(set)  # continent → set of countries
    for c in data.values():
        countries[c.country] = c + countries.get(c.country, CityData())
        continents[c.continent] = c + continents.get(c.continent, CityData())
        c_by_c[c.continent].add(c.country)
    world = sum(continents.values(), CityData())

    overground = "traml_expected" in next(iter(data.values())).data
    date = datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M UTC")
    index = open(os.path.join(target_dir, "index.html"), "w", encoding="utf-8")
    index.write(tmpl(INDEX_HEADER, world))

    for continent in sorted(continents.keys()):
        content = ""
        for country in sorted(c_by_c[continent]):
            country_file_name = country.lower().replace(" ", "-") + ".html"
            content += tmpl(
                INDEX_COUNTRY,
                countries[country],
                file=country_file_name,
                country=country,
                continent=continent,
            )
            country_file = open(
                os.path.join(target_dir, country_file_name),
                "w",
                encoding="utf-8",
            )
            country_file.write(
                tmpl(
                    COUNTRY_HEADER,
                    country=country,
                    continent=continent,
                    overground=overground,
                    subways=not overground,
                )
            )
            for name, city in sorted(
                (name, city)
                for name, city in data.items()
                if city.country == country
            ):
                file_base = os.path.join(target_dir, city.slug)
                yaml_file = (
                    city.slug + ".yaml"
                    if os.path.exists(file_base + ".yaml")
                    else None
                )
                json_file = (
                    city.slug + ".geojson"
                    if os.path.exists(file_base + ".geojson")
                    else None
                )
                errors = br_osm_links(city.errors)
                warnings = br_osm_links(city.warnings)
                notices = br_osm_links(city.notices)
                country_file.write(
                    tmpl(
                        COUNTRY_CITY,
                        city,
                        city=name,
                        country=country,
                        continent=continent,
                        yaml=yaml_file,
                        json=json_file,
                        subways=not overground,
                        errors=errors,
                        warnings=warnings,
                        notices=notices,
                        overground=overground,
                    )
                )
            country_file.write(
                tmpl(
                    COUNTRY_FOOTER,
                    country=country,
                    continent=continent,
                    date=date,
                )
            )
            country_file.close()
        index.write(
            tmpl(
                INDEX_CONTINENT,
                continents[continent],
                content=content,
                continent=continent,
            )
        )

    index.write(tmpl(INDEX_FOOTER, date=date, cities_info_url=cities_info_url))
    index.close()


if __name__ == "__main__":
    main()
