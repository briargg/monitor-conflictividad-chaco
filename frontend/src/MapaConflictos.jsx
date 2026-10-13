function MapaCalor({ conflictos }) {
  const [mapa, setMapa] = useState(null);
  const [heatLayer, setHeatLayer] = useState(null);

  useEffect(() => {
    if (!mapa) return;

    // Coordenadas de los municipios del Chaco
    const COORDS = {
      "Resistencia": [-27.4514, -58.9866],
      "Barranqueras": [-27.4833, -58.9333],
      "Fontana": [-27.4167, -58.9167],
      "Puerto Vilelas": [-27.5, -58.95],
      "Presidencia Roque Sáenz Peña": [-26.7853, -60.4389],
      "Villa Ángela": [-27.5761, -60.7136],
      "Charata": [-27.2167, -61.1833],
      "General José de San Martín": [-26.5333, -59.3333],
      "Juan José Castelli": [-25.95, -60.6167],
      "Quitilipi": [-26.8667, -60.2167],
      "Machagai": [-26.9333, -60.05],
      "Las Breñas": [-27.0833, -61.0833],
      "Tres Isletas": [-26.35, -60.4167],
      "Pampa del Indio": [-26.05, -59.9333],
      "Corzuela": [-26.95, -60.9667],
      "General Pinedo": [-27.3167, -61.2833],
      "La Leonesa": [-27.0333, -58.7],
      "Puerto Tirol": [-27.3833, -59.0833],
      "Colonia Benítez": [-27.3167, -58.9833],
      "Margarita Belén": [-27.2667, -58.9667],
    };

    // Preparar puntos del heatmap: [lat, lng, intensidad]
    const puntos = conflictos
      .map((c) => {
        const coords = COORDS[c.municipio];
        if (!coords) return null;
        // Intensidad normalizada (0-1) basada en score
        const intensidad = Math.min(1, (c.escalabilidad || 0) / 10);
        return [...coords, intensidad];
      })
      .filter(Boolean);

    if (heatLayer) {
      heatLayer.setLatLngs(puntos);
    } else {
      const layer = window.L.heatLayer(puntos, {
        radius: 35,
        blur: 25,
        maxZoom: 10,
        gradient: {
          0.2: "#00d9ff",
          0.4: "#4ade80",
          0.6: "#ffd93d",
          0.8: "#ff8c42",
          1.0: "#ff3b5c",
        },
      }).addTo(mapa);
      setHeatLayer(layer);
    }
  }, [conflictos, mapa, heatLayer]);

  useEffect(() => {
    // Inicializar mapa
    const L = window.L;
    const map = L.map("heatmap-container", {
      center: [-27.4514, -58.9866],
      zoom: 6,
      zoomControl: true,
    });

    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      {
        attribution: "© OpenStreetMap © CARTO",
        maxZoom: 18,
      }
    ).addTo(map);

    setMapa(map);

    return () => map.remove();
  }, []);

  return <div id="heatmap-container" style={{ height: "500px", width: "100%" }} />;
}