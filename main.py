from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import urllib.request
import zipfile
import numpy as np
from sklearn.neighbors import BallTree

# === Setup paths ===
GEONAMES_DIR = "/tmp/geonames"
ALL_COUNTRIES_FILE = os.path.join(GEONAMES_DIR, "allCountries.txt")
COUNTRY_INFO_FILE = os.path.join(GEONAMES_DIR, "countryInfo.txt")

# === Auto-download files if needed ===
def download_if_needed():
    os.makedirs(GEONAMES_DIR, exist_ok=True)
    if not os.path.exists(ALL_COUNTRIES_FILE):
        print("📦 Downloading allCountries.txt...")
        urllib.request.urlretrieve(
            "http://download.geonames.org/export/dump/allCountries.zip",
            f"{GEONAMES_DIR}/allCountries.zip"
        )
        with zipfile.ZipFile(f"{GEONAMES_DIR}/allCountries.zip", "r") as zip_ref:
            zip_ref.extractall(GEONAMES_DIR)

    if not os.path.exists(COUNTRY_INFO_FILE):
        print("📦 Downloading countryInfo.txt...")
        urllib.request.urlretrieve(
            "http://download.geonames.org/export/dump/countryInfo.txt",
            COUNTRY_INFO_FILE
        )

download_if_needed()

# === Load files ===
def load_geonames(file_path):
    coords = []
    names = []
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 10:
                continue
            try:
                lat = float(parts[4])
                lon = float(parts[5])
                name = parts[1]
                country = parts[8]
                coords.append([np.radians(lat), np.radians(lon)])
                names.append((name, country))
            except ValueError:
                continue
    return np.array(coords), names

def load_country_names(file_path):
    country_map = {}
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 5:
                country_code = parts[0]
                country_name = parts[4]
                country_map[country_code] = country_name
    return country_map

# === Initialize FastAPI ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🚀 Loading GeoNames data...")
coords, name_data = load_geonames(ALL_COUNTRIES_FILE)
tree = BallTree(coords, metric='haversine')
country_map = load_country_names(COUNTRY_INFO_FILE)
print("✅ GeoNames data loaded")

# === API ===
@app.get("/reverse")
def reverse_geocode(lat: float = Query(...), lon: float = Query(...)):
    point = [[np.radians(lat), np.radians(lon)]]
    dist, ind = tree.query(point, k=1)
    name, cc = name_data[ind[0][0]]
    return {
        "place": name,
        "countryCode": cc,
        "country": country_map.get(cc, cc)
    }
