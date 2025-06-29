from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from sklearn.neighbors import BallTree

# === Load GeoNames ===
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

# === Initialize once ===
coords, name_data = load_geonames("/Users/hudsonrha/Documents/allCountries.txt")
tree = BallTree(coords, metric='haversine')
country_map = load_country_names("/Users/hudsonrha/Documents/countryInfo.txt")

# === FastAPI setup ===
app = FastAPI()

# Allow all CORS for testing with Expo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
