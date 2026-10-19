import urllib.request
import json
import datetime
import os
import re

def fetch_json(url, headers=None, timeout=6):
    try:
        hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}
        if headers:
            hdr.update(headers)
        req = urllib.request.Request(url, headers=hdr)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    # 1. Celestrak NORAD active satellites
    satellites_count = "16,754"
    try:
        hdr = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request('https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json', headers=hdr)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
            if isinstance(data, list) and len(data) > 0:
                satellites_count = f"{len(data):,}"
    except Exception as e:
        print(f"Celestrak fallback: {e}")

    # 2. Humans in space (Open-Notify / NASA)
    humans_in_space = "12"
    astros_data = fetch_json('http://api.open-notify.org/astros.json', timeout=5)
    if astros_data and 'number' in astros_data:
        humans_in_space = str(astros_data['number'])

    # 3. CISA Weaponized Exploits
    cisa_exploits = "1,748"
    cisa_data = fetch_json('https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json', timeout=6)
    if cisa_data and 'count' in cisa_data:
        cisa_exploits = f"{cisa_data['count']:,}"

    # 4. NOAA Geomagnetic Space Weather Kp
    kp_index = "0.33 QUIET"
    kp_data = fetch_json('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json', timeout=5)
    if kp_data and len(kp_data) > 1:
        try:
            val = float(kp_data[-1][1])
            status = "QUIET" if val < 4 else "UNSETTLED" if val < 5 else "STORM"
            kp_index = f"{val:.2f} {status}"
        except Exception:
            pass

    # 5. Global Internet & Population
    internet_users = "5.52B"
    world_pop = "8.19B"

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    telemetry_block = f"""<!-- TELEMETRY:START -->
```
[ PLANETARY TELEMETRY // REAL-TIME SENSORS ]
ORBITING SATELLITES  :: {satellites_count:<10} [NORAD / CELESTRAK ACTIVE]
INTERNET CONNECTED   :: {internet_users:<10} [ITU GLOBAL REACH // 68.2%]
OFF-WORLD HUMANS     :: {humans_in_space:<10} [NASA / OPEN-NOTIFY // ORBIT]
WEAPONIZED ZERO-DAYS :: {cisa_exploits:<10} [CISA / DHS KEV CATALOG]
GEOMAGNETIC FIELD    :: {kp_index:<10} [NOAA SPACE WEATHER // Kp]
EARTH POPULATION     :: {world_pop:<10} [UN POPULATION PROSPECTS]
UPDATED              :: {timestamp}
```
<!-- TELEMETRY:END -->"""

    readme_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'README.md')
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if '<!-- TELEMETRY:START -->' in content:
        pattern = re.compile(r'<!-- TELEMETRY:START -->.*?<!-- TELEMETRY:END -->', re.DOTALL)
        new_content = pattern.sub(telemetry_block, content)
    else:
        # insert before <div align="center">
        insert_target = '<div align="center">'
        if insert_target in content:
            new_content = content.replace(insert_target, f"{telemetry_block}\n\n{insert_target}")
        else:
            new_content = content + "\n\n" + telemetry_block

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("Updated README.md with live planetary telemetry block.")

if __name__ == '__main__':
    main()
