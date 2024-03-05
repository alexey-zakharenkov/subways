import math

from subways.consts import MAX_DISTANCE_STOP_TO_LINE
from subways.types import LonLat, RailT


def distance(p1: LonLat, p2: LonLat) -> float:
    if p1 is None or p2 is None:
        raise Exception(
            "One of arguments to distance({}, {}) is None".format(p1, p2)
        )
    dx = math.radians(p1[0] - p2[0]) * math.cos(
        0.5 * math.radians(p1[1] + p2[1])
    )
    dy = math.radians(p1[1] - p2[1])
    return 6378137 * math.sqrt(dx * dx + dy * dy)


def is_near(p1: LonLat, p2: LonLat) -> bool:
    return (
        p1[0] - 1e-8 <= p2[0] <= p1[0] + 1e-8
        and p1[1] - 1e-8 <= p2[1] <= p1[1] + 1e-8
    )


def project_on_segment(p: LonLat, p1: LonLat, p2: LonLat) -> float | None:
    """Given three points, return u - the position of projection of
    point p onto segment p1p2 regarding point p1 and (p2-p1) direction vector
    """
    dp = (p2[0] - p1[0], p2[1] - p1[1])
    d2 = dp[0] * dp[0] + dp[1] * dp[1]
    if d2 < 1e-14:
        return None
    u = ((p[0] - p1[0]) * dp[0] + (p[1] - p1[1]) * dp[1]) / d2
    if not 0 <= u <= 1:
        return None
    return u


def project_on_line(p: LonLat, line: RailT) -> dict:
    result = {
        # In the first approximation, position on rails is the index of the
        # closest vertex of line to the point p. Fractional value means that
        # the projected point lies on a segment between two vertices.
        # More than one value can occur if a route follows the same tracks
        # more than once.
        "positions_on_line": None,
        "projected_point": None,  # (lon, lat)
    }

    if len(line) < 2:
        return result
    d_min = MAX_DISTANCE_STOP_TO_LINE * 5
    closest_to_vertex = False
    # First, check vertices in the line
    for i, vertex in enumerate(line):
        d = distance(p, vertex)
        if d < d_min:
            result["positions_on_line"] = [i]
            result["projected_point"] = vertex
            d_min = d
            closest_to_vertex = True
        elif vertex == result["projected_point"]:
            # Repeated occurrence of the track vertex in line, like Oslo Line 5
            result["positions_on_line"].append(i)
    # And then calculate distances to each segment
    for seg in range(len(line) - 1):
        # Check bbox for speed
        if not (
            (
                min(line[seg][0], line[seg + 1][0]) - MAX_DISTANCE_STOP_TO_LINE
                <= p[0]
                <= max(line[seg][0], line[seg + 1][0])
                + MAX_DISTANCE_STOP_TO_LINE
            )
            and (
                min(line[seg][1], line[seg + 1][1]) - MAX_DISTANCE_STOP_TO_LINE
                <= p[1]
                <= max(line[seg][1], line[seg + 1][1])
                + MAX_DISTANCE_STOP_TO_LINE
            )
        ):
            continue
        u = project_on_segment(p, line[seg], line[seg + 1])
        if u:
            projected_point = (
                line[seg][0] + u * (line[seg + 1][0] - line[seg][0]),
                line[seg][1] + u * (line[seg + 1][1] - line[seg][1]),
            )
            d = distance(p, projected_point)
            if d < d_min:
                result["positions_on_line"] = [seg + u]
                result["projected_point"] = projected_point
                d_min = d
                closest_to_vertex = False
            elif projected_point == result["projected_point"]:
                # Repeated occurrence of the track segment in line,
                # like Oslo Line 5
                if not closest_to_vertex:
                    result["positions_on_line"].append(seg + u)
    return result


def find_segment(
    p: LonLat, line: RailT, start_vertex: int = 0
) -> tuple[int, float] | tuple[None, None]:
    """Returns index of a segment and a position inside it."""
    EPS = 1e-9
    for seg in range(start_vertex, len(line) - 1):
        if is_near(p, line[seg]):
            return seg, 0.0
        if line[seg][0] == line[seg + 1][0]:
            if not (p[0] - EPS <= line[seg][0] <= p[0] + EPS):
                continue
            px = None
        else:
            px = (p[0] - line[seg][0]) / (line[seg + 1][0] - line[seg][0])
        if px is None or (0 <= px <= 1):
            if line[seg][1] == line[seg + 1][1]:
                if not (p[1] - EPS <= line[seg][1] <= p[1] + EPS):
                    continue
                py = None
            else:
                py = (p[1] - line[seg][1]) / (line[seg + 1][1] - line[seg][1])
            if py is None or (0 <= py <= 1):
                if py is None or px is None or (px - EPS <= py <= px + EPS):
                    return seg, px or py
    return None, None


def distance_on_line(
    p1: LonLat, p2: LonLat, line: RailT, start_vertex: int = 0
) -> tuple[float, int] | None:
    """Calculates distance via line between projections
    of points p1 and p2. Returns a TUPLE of (d, vertex):
    d is the distance and vertex is the number of the second
    vertex, to continue calculations for the next point."""
    line_len = len(line)
    seg1, pos1 = find_segment(p1, line, start_vertex)
    if seg1 is None:
        # logging.warn('p1 %s is not projected, st=%s', p1, start_vertex)
        return None
    seg2, pos2 = find_segment(p2, line, seg1)
    if seg2 is None:
        if line[0] == line[-1]:
            line = line + line[1:]
            seg2, pos2 = find_segment(p2, line, seg1)
        if seg2 is None:
            # logging.warn('p2 %s is not projected, st=%s', p2, start_vertex)
            return None
    if seg1 == seg2:
        return distance(line[seg1], line[seg1 + 1]) * abs(pos2 - pos1), seg1
    if seg2 < seg1:
        # Should not happen
        raise Exception("Pos1 %s is after pos2 %s", seg1, seg2)
    d = 0
    if pos1 < 1:
        d += distance(line[seg1], line[seg1 + 1]) * (1 - pos1)
    for i in range(seg1 + 1, seg2):
        d += distance(line[i], line[i + 1])
    if pos2 > 0:
        d += distance(line[seg2], line[seg2 + 1]) * pos2
    return d, seg2 % line_len


def angle_between(p1: LonLat, c: LonLat, p2: LonLat) -> float:
    a = round(
        abs(
            math.degrees(
                math.atan2(p1[1] - c[1], p1[0] - c[0])
                - math.atan2(p2[1] - c[1], p2[0] - c[0])
            )
        )
    )
    return a if a <= 180 else 360 - a
