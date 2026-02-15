import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useState } from "react";
import MapView from "./components/MapView";
import RoutePanel from "./components/RoutePanel";
import SummaryPanel from "./components/SummeryPanel";
import LocationFeedPage from "./pages/LocationFeedPage";
import MapLegend from "./components/maplegend";

function App() {
  const [route, setRoute] = useState<[number, number][] | null>(null);

  type SelectedLocation = {
    name: string;
    lat: number;
    lng: number;
    kind: "road" | "poi" | "pin" | "safe_poi";
  };

  const [location, setLocation] = useState<SelectedLocation | null>(null);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <>
              <RoutePanel onRouteFetched={setRoute} />

              {location && (
                <SummaryPanel
                  name={location.name}
                  lat={location.lat}
                  lng={location.lng}
                />
              )}

              <MapLegend />


              <MapView
                route={route}
                onLocationSelect={(loc) => setLocation(loc)}
              />
            </>

            
          }
        />

        <Route path="/location/:id" element={<LocationFeedPage />} />

      </Routes>
    </BrowserRouter>
  );
}

export default App;
