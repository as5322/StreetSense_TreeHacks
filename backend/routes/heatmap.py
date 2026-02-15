from fastapi import APIRouter
from fastapi.responses import Response
import math
import io
import sqlite3
import numpy as np
from PIL import Image
from db.db_writer import DBWriter
from scipy.ndimage import gaussian_filter


router = APIRouter()
db = DBWriter()

TILE_SIZE = 256

CATEGORIES = [
    "crime",
    "public_safety",
    "transport",
    "infrastructure",
    "policy",
    "protest",
    "weather",
    "other",
]

# ----------------------------
# Web Mercator helpers
# ----------------------------
EARTH_RADIUS_M = 6378137.0
EARTH_CIRCUM_M = 2.0 * math.pi * EARTH_RADIUS_M

def clamp01(v: float) -> float:
    return 0.0 if v < 0 else 1.0 if v > 1 else v

def tile_bounds_wsen(x: int, y: int, z: int):
    """
    Returns (west, south, east, north) in lon/lat for slippy tile.
    """
    n = 2.0 ** z
    west = x / n * 360.0 - 180.0
    east = (x + 1) / n * 360.0 - 180.0

    lat_rad_north = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat_rad_south = math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n)))
    north = math.degrees(lat_rad_north)
    south = math.degrees(lat_rad_south)
    return west, south, east, north

def lnglat_to_world_px(lng: float, lat: float, z: int) -> tuple[float, float]:
    """
    Slippy map global pixel coords at zoom z.
    """
    n = 2.0 ** z

    # X is linear in longitude
    x = (lng + 180.0) / 360.0 * n * TILE_SIZE

    # Clamp latitude to Mercator range
    lat = max(min(lat, 85.05112878), -85.05112878)
    lat_rad = math.radians(lat)
    y = (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n * TILE_SIZE
    return x, y

def meters_per_pixel(lat: float, z: int) -> float:
    """
    Web mercator meters-per-pixel at latitude, zoom.
    """
    lat = max(min(lat, 85.05112878), -85.05112878)
    return (EARTH_CIRCUM_M * math.cos(math.radians(lat))) / (2.0 ** z * TILE_SIZE)

# ----------------------------
# DB query
# ----------------------------
def fetch_truth_points_in_bounds(
    west: float,
    south: float,
    east: float,
    north: float,
    *,
    padding_deg: float,
    limit: int = 12000,
):
    conn = sqlite3.connect(db.path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    w = west - padding_deg
    e = east + padding_deg
    s = south - padding_deg
    n = north + padding_deg

    cur.execute(
        f"""
        SELECT lat, long, {", ".join(CATEGORIES)}
        FROM truth
        WHERE long BETWEEN ? AND ?
          AND lat BETWEEN ? AND ?
        LIMIT ?
        """,
        (w, e, s, n, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

# ----------------------------
# Risk (DB already 0..1)
# ----------------------------
def truth_to_risk01(row) -> float:
    vals = [float(row[c]) for c in CATEGORIES]  # already 0..1
    return clamp01(max(vals) if vals else 0.0)

# ----------------------------
# Heatmap rendering
# ----------------------------
def build_gaussian_kernel(sigma_px: float) -> tuple[np.ndarray, int]:
    """
    Returns (kernel, radius) where kernel shape is (2r+1, 2r+1).
    """
    radius = int(max(6, math.ceil(3.0 * sigma_px)))
    xs = np.arange(-radius, radius + 1, dtype=np.float32)
    ys = np.arange(-radius, radius + 1, dtype=np.float32)
    X, Y = np.meshgrid(xs, ys)
    kernel = np.exp(-(X * X + Y * Y) / (2.0 * sigma_px * sigma_px)).astype(np.float32)

    # Normalize kernel peak to 1 (already is), keep sum dependent on sigma (we'll compensate later)
    return kernel, radius

def render_heatmap_tile(
    z: int, x: int, y: int,
    points,
    *,
    sigma_m: float = 500.0,     # "influence radius" in meters
    strength: float = 5.0,     # global multiplier
):
    """
    Returns heat array in [0..1] (after scaling).
    """
    heat = np.zeros((TILE_SIZE, TILE_SIZE), dtype=np.float32)

    # Use tile center latitude to compute meters-per-pixel
    west, south, east, north = tile_bounds_wsen(x, y, z)
    center_lat = (south + north) * 0.5
    mpp = meters_per_pixel(center_lat, z)
    sigma_px = max(5, sigma_m / max(mpp, 1e-9))  

    kernel, radius = build_gaussian_kernel(sigma_px)

    num = np.zeros((TILE_SIZE, TILE_SIZE), dtype=np.float32)
    den = np.zeros((TILE_SIZE, TILE_SIZE), dtype=np.float32)
    # Tile origin in world pixels
    tile_origin_x = x * TILE_SIZE
    tile_origin_y = y * TILE_SIZE

    for r in points:
        lat = float(r["lat"])
        lng = float(r["long"])
        risk = truth_to_risk01(r) * strength
        if risk <= 0:
            continue

        wx, wy = lnglat_to_world_px(lng, lat, z)

        # local pixel in tile
        px = int(wx - tile_origin_x)
        py = int(wy - tile_origin_y)

        # Kernel bbox in tile coords
        x0 = px - radius
        y0 = py - radius
        x1 = px + radius
        y1 = py + radius

        # overlap with tile
        kx0 = 0
        ky0 = 0
        kx1 = kernel.shape[1] - 1
        ky1 = kernel.shape[0] - 1

        if x0 < 0:
            kx0 += -x0
            x0 = 0
        if y0 < 0:
            ky0 += -y0
            y0 = 0
        if x1 >= TILE_SIZE:
            kx1 -= (x1 - (TILE_SIZE - 1))
            x1 = TILE_SIZE - 1
        if y1 >= TILE_SIZE:
            ky1 -= (y1 - (TILE_SIZE - 1))
            y1 = TILE_SIZE - 1

        if x0 > x1 or y0 > y1:
            continue
            
        w = kernel[ky0:ky1+1, kx0:kx1+1]
        num[y0:y1+1, x0:x1+1] += risk * w
        den[y0:y1+1, x0:x1+1] += w

    heat = np.divide(num, den, out=np.zeros_like(num), where=(den > 1e-6))
    heat = np.clip(heat, 0.0, 1.0)
    heat = heat ** 0.7 

    return np.clip(heat, 0.0, 1.0)

# ----------------------------
# Color mapping (make green visible)
# ----------------------------
def heat_to_image(heat: np.ndarray) -> Image.Image:
    img = np.zeros((TILE_SIZE, TILE_SIZE, 4), dtype=np.uint8)
    v = np.clip(heat, 0.0, 1.0)

    # Smooth gradient: green -> yellow -> red
    r = (255 * v).astype(np.uint8)
    g = (255 * (1 - (v - 0.5).clip(0) * 2)).astype(np.uint8)
    b = (60 * (1 - v)).astype(np.uint8) 

    #alpha = (v ** 1.2 * 160).astype(np.uint8)
    alpha = (25 + 200 * (1 - np.exp(-3.0 * v))).astype(np.uint8)

    img[..., 0] = r
    img[..., 1] = g
    img[..., 2] = b
    img[..., 3] = alpha

    return Image.fromarray(img, mode="RGBA")


# ----------------------------
# Tile endpoint
# ----------------------------
@router.get("/tiles/{z}/{x}/{y}.png")
def heatmap_tile(z: int, x: int, y: int):
    west, south, east, north = tile_bounds_wsen(x, y, z)

    # Padding should roughly match sigma_m "bleed".
    # Convert sigma_m -> degrees latitude (~111km per degree).
    # Use ~3*sigma for bleed.
    sigma_m = 180.0
    bleed_m = 3.0 * sigma_m
    padding_deg = max(0.002, bleed_m / 111_000.0)  # ~deg lat

    points = fetch_truth_points_in_bounds(
        west, south, east, north,
        padding_deg=padding_deg,
        limit=50000
    )

    heat = render_heatmap_tile(z, x, y, points, sigma_m=sigma_m, strength=1.0)
    
    image = heat_to_image(heat)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")
