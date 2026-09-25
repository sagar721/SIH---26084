import { useEffect, useRef, useState } from "react";
import maplibregl, { type GeoJSONSource, type ImageSource, type Map as MLMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Bounds, Place } from "../types";
import { PHASE_STYLE } from "../colors";
import { renderLayer, sampleLayer, type Layer } from "../data";

const EMPTY: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
const BLANK = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=";

export class MapSync {
  private maps = new Set<MLMap>();
  private busy = false;
  add(m: MLMap) {
    this.maps.add(m);
    m.on("move", () => {
      if (this.busy) return;
      this.busy = true;
      for (const o of this.maps) if (o !== m) o.jumpTo({ center: m.getCenter(), zoom: m.getZoom(), bearing: 0, pitch: 0 });
      this.busy = false;
    });
  }
  remove(m: MLMap) { this.maps.delete(m); }
}

export interface MapProps {
  event: string;
  bounds: Bounds;
  layer: Layer | null;
  threshold?: number;
  cells?: GeoJSON.FeatureCollection | null;
  contours?: GeoJSON.FeatureCollection | null;
  arrows?: GeoJSON.FeatureCollection | null;
  pastTrack?: [number, number][] | null;
  fcTrack?: { coords: [number, number][]; labels: string[] } | null;
  places?: (Place & { p?: number })[];
  selectedCell?: number | null;
  onCellClick?: (cell: number) => void;
  basemap?: boolean;
  sync?: MapSync;
  title?: string;
  badge?: string;
}

export default function MapView(props: MapProps) {
  const el = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MLMap | null>(null);
  const [ready, setReady] = useState(false);
  const [readout, setReadout] = useState<string>("");
  const markers = useRef<maplibregl.Marker[]>([]);
  const latest = useRef(props);
  latest.current = props;

  useEffect(() => {
    const b = props.bounds;
    const map = new maplibregl.Map({
      container: el.current!,
      style: {
        version: 8,
        sources: {
          // Esri World Light Gray Canvas: neutral light basemap, no API key (CARTO tiles now return "API KEY REQUIRED").
          basemap: { type: "raster", tileSize: 256, maxzoom: 16,
                     attribution: "Tiles © Esri — Esri, HERE, Garmin, © OpenStreetMap contributors",
                     tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"] },
        },
        layers: [{ id: "bg", type: "background", paint: { "background-color": "#EDE7DC" } },
                 { id: "basemap", type: "raster", source: "basemap", paint: { "raster-opacity": 0.9 } }],
      },
      bounds: [[b.west, b.south], [b.east, b.north]],
      fitBoundsOptions: { padding: 10 },
      maxBounds: [[b.west - 6, b.south - 5], [b.east + 6, b.north + 5]],
      attributionControl: { compact: true },
      dragRotate: false,
      pitchWithRotate: false,
    });
    map.touchZoomRotate.disableRotation();
    // Superseded image/tile requests are cancelled by MapLibre (AbortError) during playback or screen changes; that is
    // expected. Anything else is still reported.
    map.on("error", (e) => {
      const err = e.error as { name?: string; message?: string } | undefined;
      if (err?.name === "AbortError" || /abort/i.test(err?.message ?? "")) return;
      console.error(err ?? e);
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-right");
    map.on("load", () => {
      map.addSource("field", { type: "image", url: BLANK,
        coordinates: [[b.west, b.north], [b.east, b.north], [b.east, b.south], [b.west, b.south]] });
      map.addLayer({ id: "field", type: "raster", source: "field", paint: { "raster-resampling": "nearest", "raster-opacity": 0.9,
                                                                             "raster-fade-duration": 0 } });
      map.addSource("domain", { type: "geojson", data: { type: "Feature", properties: {}, geometry: { type: "LineString",
        coordinates: [[b.west, b.south], [b.east, b.south], [b.east, b.north], [b.west, b.north], [b.west, b.south]] } } });
      map.addLayer({ id: "domain", type: "line", source: "domain", paint: { "line-color": "#1F2A44", "line-width": 1, "line-dasharray": [3, 3] } });
      for (const id of ["contours", "cells", "arrows", "track", "fctrack", "fcpts"]) map.addSource(id, { type: "geojson", data: EMPTY });
      map.addLayer({ id: "contours", type: "line", source: "contours", paint: { "line-color": "#111", "line-width": 1.2 } });
      map.addLayer({ id: "cells-fill", type: "fill", source: "cells", paint: {
        "fill-color": ["match", ["get", "phase"], ...Object.entries(PHASE_STYLE).flatMap(([k, v]) => [k, v.color]), "#6B6457"] as unknown as string,
        "fill-opacity": 0.16 } });
      for (const [phase, st] of Object.entries(PHASE_STYLE)) {
        map.addLayer({ id: `cells-${phase}`, type: "line", source: "cells", filter: ["==", ["get", "phase"], phase],
                       paint: { "line-color": st.color, "line-width": st.width, "line-dasharray": st.dash } });
      }
      map.addLayer({ id: "cells-selected", type: "line", source: "cells", filter: ["==", ["get", "cell"], -1],
                     paint: { "line-color": "#1F2A44", "line-width": 3.5 } });
      map.addLayer({ id: "arrows", type: "line", source: "arrows", paint: { "line-color": "#1F2A44", "line-width": 1.6 } });
      map.addLayer({ id: "track", type: "line", source: "track", paint: { "line-color": "#1F2A44", "line-width": 2.2 } });
      map.addLayer({ id: "fctrack", type: "line", source: "fctrack", paint: { "line-color": "#B23A2E", "line-width": 2, "line-dasharray": [2, 1.5] } });
      map.addLayer({ id: "fcpts", type: "circle", source: "fcpts", paint: { "circle-radius": 4, "circle-color": "#FBF8F3",
                                                                          "circle-stroke-color": "#B23A2E", "circle-stroke-width": 2 } });
      map.on("click", "cells-fill", (e) => {
        const f = e.features?.[0];
        if (f && latest.current.onCellClick) latest.current.onCellClick(Number(f.properties?.cell));
      });
      map.on("mouseenter", "cells-fill", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "cells-fill", () => (map.getCanvas().style.cursor = ""));
      map.on("mousemove", async (e) => {
        const p = latest.current;
        const cell = map.queryRenderedFeatures(e.point, { layers: ["cells-fill"] })[0];
        let txt = `${e.lngLat.lat.toFixed(2)}°N ${e.lngLat.lng.toFixed(2)}°E`;
        if (p.layer) {
          const v = await sampleLayer(p.event, p.layer, e.lngLat.lng, e.lngLat.lat, p.bounds);
          txt += p.layer.kind === "ml" ? ` · P=${v === null ? "no data" : v.toFixed(2)}` : ` · BT=${v === null ? "no data" : `${v} K`}`;
        }
        if (cell) txt += ` · cell #${cell.properties?.cell} (${cell.properties?.phase})`;
        setReadout(txt);
      });
      setReady(true);
    });
    const ro = new ResizeObserver(() => map.resize());
    ro.observe(el.current!);
    mapRef.current = map;
    props.sync?.add(map);
    return () => {
      props.sync?.remove(map);
      ro.disconnect();
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // raster
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    let cancelled = false;
    const src = map.getSource("field") as ImageSource;
    const b = props.bounds;
    const coords: [[number, number], [number, number], [number, number], [number, number]] =
      [[b.west, b.north], [b.east, b.north], [b.east, b.south], [b.west, b.south]];
    if (!props.layer) { src.updateImage({ url: BLANK, coordinates: coords }); return; }
    renderLayer(props.event, props.layer, props.threshold ?? 0.1)
      .then((url) => { if (!cancelled) src.updateImage({ url, coordinates: coords }); })
      .catch(() => { if (!cancelled) src.updateImage({ url: BLANK, coordinates: coords }); });
    return () => { cancelled = true; };
  }, [ready, props.event, JSON.stringify(props.layer), props.threshold, props.bounds]);

  // vectors
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    (map.getSource("cells") as GeoJSONSource).setData(props.cells ?? EMPTY);
    (map.getSource("contours") as GeoJSONSource).setData(props.contours ?? EMPTY);
    (map.getSource("arrows") as GeoJSONSource).setData(props.arrows ?? EMPTY);
    map.setFilter("cells-selected", ["==", ["get", "cell"], props.selectedCell ?? -1]);
    const line = (c?: [number, number][] | null): GeoJSON.FeatureCollection =>
      c && c.length > 1 ? { type: "FeatureCollection", features: [{ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: c } }] } : EMPTY;
    (map.getSource("track") as GeoJSONSource).setData(line(props.pastTrack));
    (map.getSource("fctrack") as GeoJSONSource).setData(line(props.fcTrack?.coords));
    (map.getSource("fcpts") as GeoJSONSource).setData({ type: "FeatureCollection", features: (props.fcTrack?.coords ?? []).slice(1).map((c) => (
      { type: "Feature", properties: {}, geometry: { type: "Point", coordinates: c } })) });
  }, [ready, props.cells, props.contours, props.arrows, props.selectedCell, props.pastTrack, props.fcTrack]);

  // basemap toggle
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    map.setLayoutProperty("basemap", "visibility", props.basemap === false ? "none" : "visible");
  }, [ready, props.basemap]);

  // HTML markers: places + forecast lead labels (no glyph server needed; works offline)
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    markers.current.forEach((m) => m.remove());
    markers.current = [];
    for (const p of props.places ?? []) {
      const d = document.createElement("div");
      const risk = p.p ?? 0;
      d.className = `place-marker ${risk >= 0.5 ? "risk-high" : risk >= 0.3 ? "risk-med" : ""}`;
      d.title = `${p.name} (IMD hail report ${p.report_date})${p.p !== undefined ? ` · max ML P next 60 min ${p.p.toFixed(2)}` : ""}`;
      d.innerHTML = `<span class="dot"></span><span class="lbl">${p.name}${p.p !== undefined && p.p >= 0.3 ? ` ${p.p.toFixed(2)}` : ""}</span>`;
      markers.current.push(new maplibregl.Marker({ element: d, anchor: "left" }).setLngLat([p.lon, p.lat]).addTo(map));
    }
    const fc = props.fcTrack;
    fc?.coords.slice(1).forEach((c, i) => {
      const d = document.createElement("div");
      d.className = "lead-marker";
      d.textContent = fc.labels[i];
      markers.current.push(new maplibregl.Marker({ element: d, anchor: "bottom-left", offset: [6, -4] }).setLngLat(c).addTo(map));
    });
  }, [ready, props.places, props.fcTrack]);

  return (
    <div className="map-wrap">
      {props.title && <div className="map-title">{props.title}{props.badge && <span className="badge badge-muted">{props.badge}</span>}</div>}
      <div ref={el} className="map" />
      <div className="map-readout mono">{readout}</div>
    </div>
  );
}
