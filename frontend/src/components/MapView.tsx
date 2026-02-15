import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
// import HeatmapToggle from "./HeatmapToggle";
import MapHeader from "./MapHeader";
import "mapbox-gl/dist/mapbox-gl.css";

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

type SelectedLocation = {
  name: string;
  lat: number;
  lng: number;
  kind: "road" | "poi" | "pin" | "safe_poi";
};

type Props = {
  route: [number, number][] | null;
  onLocationSelect: (location: SelectedLocation) => void;
};



const RASTER_SOURCE_ID = "safety-raster-source";
const RASTER_LAYER_ID = "safety-raster-layer";

export default function MapView({ route, onLocationSelect }: Props) {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const safeMarkersRef = useRef<mapboxgl.Marker[]>([]);
  const lastPickedRef = useRef<{ lat: number; lng: number } | null>(null);

  function clearSafeMarkers() {
    for (const m of safeMarkersRef.current) m.remove();
    safeMarkersRef.current = [];
  }

  const [showHeatmap, setShowHeatmap] = useState(false);

  const toggleHeatmap = () => {
    setShowHeatmap((prev) => !prev);
  };

  // =========================
  // MAP INITIALISATION
  // =========================
  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/streets-v12",
      center: [-0.1276, 51.5074],
      zoom: 12,
    });

    map.addControl(new mapboxgl.NavigationControl());
    mapRef.current = map;

    map.on("load", () => {
      addRasterHeatmap(map);

      map.addLayer({
        id: "landmarks",
        type: "symbol",
        source: "composite",
        "source-layer": "poi_label",
        layout: {
          "text-field": ["get", "name"],
          "text-size": 12,
        },
        paint: {
          "text-color": "#333",
        },
      });
    });
    map.on("click", (e) => {
  const features = map.queryRenderedFeatures(e.point);

  const pickFromLayers = (layerIds: string[]) => {
    for (const f of features) {
      const id = f.layer?.id;
      if (!id || !layerIds.includes(id)) continue;

      const name =
        (f.properties?.name as string | undefined) ||
        (f.properties?.ref as string | undefined);

      if (name && name.trim()) return name;
    }
    return undefined;
  };

  const roadName = pickFromLayers([
    "road-label",
    "road-label-simple",
    "road-label-navigation",
    "road-number-shield",
  ]);

  const poiName =
    pickFromLayers(["landmarks", "poi-label", "poi-labels"]) ??
    (features.find((f) => typeof f.properties?.name === "string")?.properties
      ?.name as string | undefined);

  const name = roadName || poiName || "Dropped Pin";

  const lat = e.lngLat.lat;
  const lng = e.lngLat.lng;

  lastPickedRef.current = { lat, lng };


  onLocationSelect({
    name,
    lat,
    lng,
    kind: roadName ? "road" : poiName ? "poi" : "pin",
  });
});



    return () => {
      map.remove();
    };
  }, []);

  // =========================
  // HEATMAP TOGGLE
  // =========================
  useEffect(() => {
    if (!mapRef.current) return;

    const map = mapRef.current;

    if (map.getLayer(RASTER_LAYER_ID)) {
      map.setPaintProperty(
        RASTER_LAYER_ID,
        "raster-opacity",
        showHeatmap ? 0.7 : 0
      );
    }
  }, [showHeatmap]);

  // =========================
  // ROUTE RENDERING
  // =========================
  useEffect(() => {
    if (!mapRef.current || !route || route.length === 0) return;

    const map = mapRef.current;

    const geojson = {
      type: "Feature" as const,
      geometry: {
        type: "LineString" as const,
        coordinates: route,
      },
      properties: {},
    };

    if (map.getSource("route")) {
      (map.getSource("route") as mapboxgl.GeoJSONSource).setData(geojson);
    } else {
      map.addSource("route", {
        type: "geojson",
        data: geojson,
      });

      map.addLayer({
        id: "route",
        type: "line",
        source: "route",
        paint: {
          "line-color": "#007AFF",
          "line-width": 5,
        },
      });
    }

    const bounds = new mapboxgl.LngLatBounds();
    route.forEach((coord) => bounds.extend(coord));

    map.fitBounds(bounds, {
      padding: 80,
      duration: 1000,
    });
  }, [route]);

  return (
    <>
      <MapHeader
    showHeatmap={showHeatmap}
    toggleHeatmap={toggleHeatmap}
    onShowNearbySafe={() => {
  
  
          if (!mapRef.current) return;

    const map = mapRef.current;

    // anchor = last clicked location, fallback to map center
    const anchor =
      lastPickedRef.current ??
      (() => {
        const c = map.getCenter();
        return { lat: c.lat, lng: c.lng };
      })();

    clearSafeMarkers();
    const fake = generateSafeLocations(anchor.lat, anchor.lng, 50);

    fake.forEach((loc) => {
      const popup = new mapboxgl.Popup({ offset: 18 }).setHTML(
        `<div style="font-weight:800;margin-bottom:4px">${escapeHtml(
          loc.name
        )}</div>`
      );

      const marker = new mapboxgl.Marker({ color: loc.color })
        .setLngLat([loc.lng, loc.lat])
        .setPopup(popup)
        .addTo(map);

      // When marker element is clicked: set destination in your UI
      marker.getElement().addEventListener("click", (e) => {
        e.stopPropagation();

        // auto-fill destination (your parent decides what to do with it)
        onLocationSelect({
          name: loc.name,
          lat: loc.lat,
          lng: loc.lng,
          kind: "safe_poi",
        });

        // optional: fly to it + open popup
        map.easeTo({ center: [loc.lng, loc.lat], zoom: Math.max(map.getZoom(), 14) });
        marker.togglePopup();
      });

      safeMarkersRef.current.push(marker);
    });
    
  
  
  
  
  }}





    onResetRoute={() => {
      if (!mapRef.current) return;

      clearSafeMarkers(); 

      const map = mapRef.current;

      if (map.getLayer("route")) {
        map.removeLayer("route");
      }

      if (map.getSource("route")) {
        map.removeSource("route");
      }
    }}
    />

      <div
        ref={mapContainer}
        style={{ width: "100vw", height: "100vh" }}
      />
    </>
  );
}

// =========================
// RASTER HEATMAP
// =========================

function addRasterHeatmap(map: mapboxgl.Map) {
  const tileUrl =
    "http://127.0.0.1:8000/tiles/{z}/{x}/{y}.png";

  if (!map.getSource(RASTER_SOURCE_ID)) {
    map.addSource(RASTER_SOURCE_ID, {
      type: "raster",
      tiles: [tileUrl],
      tileSize: 256,
    });
  }

  if (!map.getLayer(RASTER_LAYER_ID)) {
    map.addLayer({
      id: RASTER_LAYER_ID,
      type: "raster",
      source: RASTER_SOURCE_ID,
      paint: {
        "raster-opacity": 0,
      },
    });
  }
}

type Safe = {
  name: string;
  lat: number;
  lng: number;
  color: string;
};

function generateSafeLocations(anchorLat: number, anchorLng: number, n = 20): Safe[] {
  const kinds = [
    { kind: "Police Station", color: "#2563eb" },
    { kind: "24 Hour Store", color: "#16a34a" },
    { kind: "Hospital", color: "#dc2626" },
    { kind: "Pub", color: "#f59e0b" },
  ];

  const out: Safe[] = [];
  for (let i = 0; i < n; i++) {
    const k = kinds[Math.floor(Math.random() * kinds.length)];

    const { lat, lng } = randomPointAround(anchorLat, anchorLng, 12000);

    out.push({
      name: `${k.kind} ${i + 1}`,
      lat,
      lng,
      color: k.color,
    });
  }
  return out;
}

// Uniform-ish random point inside circle (meters)
function randomPointAround(lat: number, lng: number, radiusMeters: number) {
  const r = radiusMeters * Math.sqrt(Math.random());
  const theta = Math.random() * 2 * Math.PI;

  const dx = r * Math.cos(theta);
  const dy = r * Math.sin(theta);

  // meters -> degrees
  const dLat = dy / 111_320;
  const dLng = dx / (111_320 * Math.cos((lat * Math.PI) / 180));

  return { lat: lat + dLat, lng: lng + dLng };
}

function escapeHtml(s: string) {
  return s.replace(/[&<>"']/g, (c) => {
    switch (c) {
      case "&":
        return "&amp;";
      case "<":
        return "&lt;";
      case ">":
        return "&gt;";
      case '"':
        return "&quot;";
      case "'":
        return "&#039;";
      default:
        return c;
    }
  });
}
