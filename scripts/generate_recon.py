import math
import random
import os
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont

def fetch_json(url, timeout=5):
    try:
        hdr = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=hdr)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return None

def rotate_point(x, y, z, pitch, yaw):
    x1 = x * math.cos(yaw) + z * math.sin(yaw)
    y1 = y
    z1 = -x * math.sin(yaw) + z * math.cos(yaw)
    
    x2 = x1
    y2 = y1 * math.cos(pitch) - z1 * math.sin(pitch)
    z2 = y1 * math.sin(pitch) + z1 * math.cos(pitch)
    return x2, y2, z2

def get_earth_land_points():
    points = []
    regions = [
        # North America
        (25, 60, -125, -75, 45),
        (55, 75, -165, -120, 20),
        # South America
        (-50, 10, -75, -40, 40),
        # Europe
        (38, 65, -10, 40, 40),
        # Africa
        (-32, 35, -15, 48, 55),
        # Asia
        (15, 70, 45, 140, 95),
        (8, 28, 70, 88, 30),
        # Australia
        (-38, -15, 115, 150, 25),
        # Japan
        (30, 45, 130, 145, 12),
        # UK
        (50, 58, -10, 2, 10),
    ]
    random.seed(1337)
    for lat_min, lat_max, lon_min, lon_max, count in regions:
        for _ in range(count):
            lat = math.radians(random.uniform(lat_min, lat_max))
            lon = math.radians(random.uniform(lon_min, lon_max))
            points.append((lat, lon))
    return points

def generate_sphere_wireframe(radius, lat_count=7, lon_count=10, points_per_line=32):
    lines = []
    for i in range(1, lat_count):
        lat = -math.pi/2 + (i * math.pi / lat_count)
        r_lat = radius * math.cos(lat)
        y = radius * math.sin(lat)
        line = []
        for j in range(points_per_line):
            lon = j * 2 * math.pi / points_per_line
            x = r_lat * math.sin(lon)
            z = r_lat * math.cos(lon)
            line.append((x, y, z))
        lines.append(line)
        
    for i in range(lon_count):
        lon = i * math.pi / lon_count
        line = []
        for j in range(points_per_line):
            lat = j * 2 * math.pi / points_per_line
            x = radius * math.cos(lat) * math.sin(lon)
            y = radius * math.sin(lat)
            z = radius * math.cos(lat) * math.cos(lon)
            line.append((x, y, z))
        lines.append(line)
    return lines

def generate_orbit(orbit_radius, inclination_deg, points_count=48):
    inclination = math.radians(inclination_deg)
    line = []
    for i in range(points_count):
        theta = i * 2 * math.pi / points_count
        x = orbit_radius * math.cos(theta)
        y = orbit_radius * math.sin(theta) * math.sin(inclination)
        z = orbit_radius * math.sin(theta) * math.cos(inclination)
        line.append((x, y, z))
    return line

def get_font(size):
    candidate_paths = [
        "/home/rdev/.local/share/fonts/apple-sf/LigaSFMonoNerdFont-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def fetch_telemetry():
    # 1. Celestrak
    satellites = "16,754 ACTIVE"
    try:
        hdr = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request('https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json', headers=hdr)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if isinstance(data, list) and len(data) > 0:
                satellites = f"{len(data):,} ACTIVE"
    except Exception:
        pass

    # 2. Open-Notify (NASA)
    crew = "12 SOULS"
    astros = fetch_json('http://api.open-notify.org/astros.json', timeout=5)
    if astros and 'number' in astros:
        crew = f"{astros['number']} SOULS"

    # 3. CISA
    cisa = "1,748 CVEs"
    cisa_data = fetch_json('https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json', timeout=5)
    if cisa_data and 'count' in cisa_data:
        cisa = f"{cisa_data['count']:,} CVEs"

    # 4. NOAA
    kp_val = "0.33 Kp NORMAL"
    kp_data = fetch_json('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json', timeout=5)
    if kp_data and len(kp_data) > 1:
        try:
            val = float(kp_data[-1][1])
            status = "NORMAL" if val < 4 else "UNSETTLED" if val < 5 else "STORM"
            kp_val = f"{val:.2f} Kp {status}"
        except Exception:
            pass

    return {
        "satellites": satellites,
        "crew": crew,
        "internet": "5.52B (68.2%)",
        "cisa": cisa,
        "kp": kp_val,
        "pop": "8.19B SOULS"
    }

def main():
    W, H = 720, 240
    globe_cx, globe_cy = 115, 120
    radius = 68
    orbit_iss_r = 84
    orbit_geo_r = 98
    pitch = math.radians(23.4)
    
    font_title = get_font(11)
    font_body = get_font(10)
    font_data = get_font(10)
    font_small = get_font(8)
    
    sphere_lines = generate_sphere_wireframe(radius, lat_count=7, lon_count=10, points_per_line=32)
    land_points = get_earth_land_points()
    
    land_3d = []
    for lat, lon in land_points:
        x = radius * math.cos(lat) * math.sin(lon)
        y = -radius * math.sin(lat)
        z = radius * math.cos(lat) * math.cos(lon)
        land_3d.append((x, y, z))
        
    iss_orbit = generate_orbit(orbit_iss_r, 51.6, points_count=36)
    geo_orbit = generate_orbit(orbit_geo_r, 0, points_count=36)
    
    telem = fetch_telemetry()
    
    rows = [
        ("SATELLITES IN ORBIT", telem["satellites"], "#10b981", "NORAD / CELESTRAK"),
        ("CREW OFF-WORLD",      telem["crew"],       "#38bdf8", "NASA / TIANGONG"),
        ("INTERNET CONNECTED",  telem["internet"],   "#f1f5f9", "ITU GLOBAL REACH"),
        ("WEAPONIZED ZERO-DAYS",telem["cisa"],       "#f43f5e", "CISA KEV CATALOG"),
        ("GEOMAGNETIC STORM",   telem["kp"],         "#c084fc", "NOAA SPACE WEATHER"),
        ("PLANETARY CENSUS",    telem["pop"],        "#94a3b8", "UN POP. PROSPECTS")
    ]
    
    frames = []
    total_frames = 36
    
    for frame_idx in range(total_frames):
        yaw = frame_idx * (2 * math.pi / total_frames)
        img = Image.new("RGB", (W, H), "#080c14")
        draw = ImageDraw.Draw(img)
        
        # Border
        draw.rounded_rectangle([5, 5, W-6, H-6], radius=6, outline="#1e293b", width=1)
        
        # Crosshair marks around globe
        draw.line([globe_cx - 95, globe_cy, globe_cx - 82, globe_cy], fill="#1e293b", width=1)
        draw.line([globe_cx + 82, globe_cy, globe_cx + 95, globe_cy], fill="#1e293b", width=1)
        draw.line([globe_cx, globe_cy - 95, globe_cx, globe_cy - 82], fill="#1e293b", width=1)
        draw.line([globe_cx, globe_cy + 82, globe_cx, globe_cy + 95], fill="#1e293b", width=1)
        
        # 1. GEO Orbit ring
        for i in range(len(geo_orbit)):
            p1 = geo_orbit[i]
            p2 = geo_orbit[(i + 1) % len(geo_orbit)]
            rx1, ry1, rz1 = rotate_point(p1[0], p1[1], p1[2], pitch, yaw * 0.1)
            rx2, ry2, rz2 = rotate_point(p2[0], p2[1], p2[2], pitch, yaw * 0.1)
            col = "#0f172a" if rz1 < 0 else "#1e293b"
            draw.line([globe_cx + rx1, globe_cy + ry1, globe_cx + rx2, globe_cy + ry2], fill=col, width=1)

        # 2. ISS Orbit ring
        for i in range(len(iss_orbit)):
            p1 = iss_orbit[i]
            p2 = iss_orbit[(i + 1) % len(iss_orbit)]
            rx1, ry1, rz1 = rotate_point(p1[0], p1[1], p1[2], pitch, 0)
            rx2, ry2, rz2 = rotate_point(p2[0], p2[1], p2[2], pitch, 0)
            col = "#111827" if rz1 < 0 else "#334155"
            draw.line([globe_cx + rx1, globe_cy + ry1, globe_cx + rx2, globe_cy + ry2], fill=col, width=1)

        # 3. Sphere Wireframe - back
        for line in sphere_lines:
            rotated = [rotate_point(pt[0], pt[1], pt[2], pitch, yaw) for pt in line]
            for i in range(len(rotated)):
                p1 = rotated[i]
                p2 = rotated[(i + 1) % len(rotated)]
                if p1[2] <= 0 and p2[2] <= 0:
                    draw.line([globe_cx + p1[0], globe_cy + p1[1], globe_cx + p2[0], globe_cy + p2[1]], fill="#0f1f33", width=1)

        # 4. Landmass dots - back
        for pt in land_3d:
            rx, ry, rz = rotate_point(pt[0], pt[1], pt[2], pitch, yaw)
            if rz <= 0:
                draw.point((globe_cx + rx, globe_cy + ry), fill="#064e3b")

        # 5. Sphere Wireframe - front
        for line in sphere_lines:
            rotated = [rotate_point(pt[0], pt[1], pt[2], pitch, yaw) for pt in line]
            for i in range(len(rotated)):
                p1 = rotated[i]
                p2 = rotated[(i + 1) % len(rotated)]
                if p1[2] > 0 or p2[2] > 0:
                    depth = max(0.1, (p1[2] + radius) / (2 * radius))
                    g = int(70 + 120 * depth)
                    b = int(130 + 115 * depth)
                    r = int(10 + 25 * depth)
                    draw.line([globe_cx + p1[0], globe_cy + p1[1], globe_cx + p2[0], globe_cy + p2[1]], fill=(r, g, b), width=1)

        # 6. Landmass dots - front
        for pt in land_3d:
            rx, ry, rz = rotate_point(pt[0], pt[1], pt[2], pitch, yaw)
            if rz > 0:
                depth = (rz + radius) / (2 * radius)
                if depth > 0.65:
                    px, py = globe_cx + rx, globe_cy + ry
                    draw.rectangle([px-1, py-1, px+1, py+1], fill="#34d399")
                else:
                    draw.point((globe_cx + rx, globe_cy + ry), fill="#10b981")

        # 7. Orbiting Satellites
        iss_idx = int((frame_idx * 1.5) % len(iss_orbit))
        iss_p = iss_orbit[iss_idx]
        ix, iy, iz = rotate_point(iss_p[0], iss_p[1], iss_p[2], pitch, 0)
        iss_screen_x = globe_cx + ix
        iss_screen_y = globe_cy + iy
        
        draw.ellipse([iss_screen_x - 3, iss_screen_y - 3, iss_screen_x + 3, iss_screen_y + 3], fill="#f43f5e", outline="#ffffff", width=1)
        lbl_x = iss_screen_x - 42 if iss_screen_x > globe_cx else iss_screen_x + 6
        draw.text((lbl_x, iss_screen_y - 5), "ISS", fill="#fb7185", font=font_small)

        # Commsat
        geo_idx = int((frame_idx * 2.2) % len(geo_orbit))
        gp = geo_orbit[geo_idx]
        gx, gy, gz = rotate_point(gp[0], gp[1], gp[2], pitch, yaw * 0.1)
        draw.ellipse([globe_cx + gx - 2, globe_cy + gy - 2, globe_cx + gx + 2, globe_cy + gy + 2], fill="#38bdf8", outline="#ffffff", width=1)

        draw.text((globe_cx - 40, H - 22), "SOL-3 // ORBITAL", fill="#475569", font=font_small)

        # Vertical divider line
        div_x = 228
        draw.line([div_x, 16, div_x, H - 17], fill="#1e293b", width=1)

        # Right side: Terminal Telemetry HUD
        tx = div_x + 22
        ty = 20
        
        draw.text((tx, ty), "[ ORBITAL RECON // REAL-TIME TELEMETRY ]", fill="#38bdf8", font=font_title)
        draw.line([tx, ty + 18, W - 20, ty + 18], fill="#1e293b", width=1)
        
        curr_y = ty + 25
        for label, val, val_col, src in rows:
            draw.text((tx, curr_y), f"{label:<21} ::", fill="#64748b", font=font_body)
            draw.text((tx + 165, curr_y), val, fill=val_col, font=font_data)
            draw.text((tx + 300, curr_y), f"[{src}]", fill="#475569", font=font_small)
            curr_y += 23
            
        # Status footer
        draw.line([tx, H - 30, W - 20, H - 30], fill="#1e293b", width=1)
        draw.text((tx, H - 22), "FEED: REAL-TIME SYNC", fill="#10b981", font=font_small)
        draw.text((tx + 175, H - 22), "TARGET: SOL-3 // LEO", fill="#475569", font=font_small)
        draw.text((W - 120, H - 22), "STATUS: SCANNING", fill="#64748b", font=font_small)

        frames.append(img.quantize(colors=48, method=Image.Resampling.LANCZOS))
        
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'orbital_recon.gif')
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=45,
        loop=0,
        optimize=True
    )
    print(f"Generated orbital recon GIF at {output_path} ({os.path.getsize(output_path)} bytes)")

if __name__ == '__main__':
    main()
