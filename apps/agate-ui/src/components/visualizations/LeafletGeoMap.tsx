import { useCallback, useEffect, useMemo, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { GeoJSON, MapContainer, TileLayer, useMap } from 'react-leaflet'
import type { Feature, FeatureCollection, GeoJsonObject, Polygon, MultiPolygon } from 'geojson'

import type { MapBoundingBoxFeature, MapPointFeature } from '@/lib/visualizations'

type LeafletGeoMapProps = {
  points: MapPointFeature[]
  polygons: MapBoundingBoxFeature[]
  height?: number
}

const DEFAULT_CENTER: L.LatLngExpression = [39.8283, -98.5795]
const POINT_FLY_ZOOM = 13
const MAX_ZOOM_FIT = 12
const MAX_ZOOM_ROW = 14

type LegendGroup = {
  id: string
  type: 'polygon' | 'point'
  label: string
}

function createPolygonCoordinates([west, south, east, north]: [
  number,
  number,
  number,
  number,
]): number[][] {
  return [
    [west, south],
    [east, south],
    [east, north],
    [west, north],
    [west, south],
  ]
}

function extendBoundsWithGeometry(bounds: L.LatLngBounds, geom: Polygon | MultiPolygon): boolean {
  let has = false
  const extendCoord = (coord: number[]) => {
    if (Array.isArray(coord) && coord.length >= 2) {
      bounds.extend([coord[1], coord[0]])
      has = true
    }
  }
  if (geom.type === 'Polygon') {
    geom.coordinates[0]?.forEach(extendCoord)
  } else {
    for (const polygon of geom.coordinates) {
      polygon[0]?.forEach(extendCoord)
    }
  }
  return has
}

function getLeafletBounds(points: MapPointFeature[], polygons: MapBoundingBoxFeature[]): L.LatLngBounds | null {
  const bounds = L.latLngBounds([] as L.LatLngTuple[])
  let hasBounds = false

  points.forEach((point) => {
    bounds.extend([point.coordinates[1], point.coordinates[0]])
    hasBounds = true
  })

  polygons.forEach((polygon) => {
    if (polygon.geometry) {
      if (extendBoundsWithGeometry(bounds, polygon.geometry as Polygon | MultiPolygon)) {
        hasBounds = true
      }
    } else {
      const [west, south, east, north] = polygon.bbox
      bounds.extend([south, west])
      bounds.extend([north, east])
      hasBounds = true
    }
  })

  return hasBounds && bounds.isValid() ? bounds : null
}

function boundsForPolygonGeometry(geometry: Polygon | MultiPolygon): L.LatLngBounds | null {
  const bounds = L.latLngBounds([] as L.LatLngTuple[])
  if (!extendBoundsWithGeometry(bounds, geometry)) {
    return null
  }
  return bounds.isValid() ? bounds : null
}

function FitBoundsOnData({
  bounds,
  boundsKey,
}: {
  bounds: L.LatLngBounds | null
  boundsKey: string
}) {
  const map = useMap()
  useEffect(() => {
    if (bounds?.isValid()) {
      map.fitBounds(bounds, { padding: [48, 48], maxZoom: MAX_ZOOM_FIT, animate: false })
    } else {
      map.setView(DEFAULT_CENTER, 2.5, { animate: false })
    }
  }, [map, bounds, boundsKey])
  return null
}

function InvalidateOnResize({ height }: { height: number }) {
  const map = useMap()
  useEffect(() => {
    const el = map.getContainer()
    const ro = new ResizeObserver(() => {
      map.invalidateSize()
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [map])
  useEffect(() => {
    map.invalidateSize()
  }, [map, height])
  return null
}

type FlyToPayload = { id: string; type: 'Point' | 'Polygon'; nonce: number }

function FlyToOnRequest({
  request,
  points,
  polygons,
  onDone,
}: {
  request: FlyToPayload | null
  points: MapPointFeature[]
  polygons: MapBoundingBoxFeature[]
  onDone: () => void
}) {
  const map = useMap()
  useEffect(() => {
    if (!request) return
    const { id, type } = request
    if (type === 'Point') {
      const pt = points.find((p) => p.id === id)
      if (pt) {
        map.flyTo([pt.coordinates[1], pt.coordinates[0]], POINT_FLY_ZOOM, { duration: 0.5 })
      }
    } else {
      const poly = polygons.find((p) => p.id === id)
      if (poly) {
        let b: L.LatLngBounds | null = null
        if (poly.geometry) {
          b = boundsForPolygonGeometry(poly.geometry as Polygon | MultiPolygon)
        }
        if (!b?.isValid()) {
          const [w, s, e, n] = poly.bbox
          b = L.latLngBounds([s, w], [n, e])
        }
        if (b?.isValid()) {
          map.fitBounds(b, { padding: [48, 48], maxZoom: MAX_ZOOM_ROW, animate: true })
        }
      }
    }
    onDone()
  }, [request, map, points, polygons, onDone])
  return null
}

function escapeHtml(s: string) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function popupHtml(title: string, description?: string) {
  const safeTitle = escapeHtml(title)
  const descBlock = description
    ? `<div class="mt-1 text-xs text-muted-foreground">${escapeHtml(description)}</div>`
    : ''
  return `<div class="text-sm"><strong>${safeTitle}</strong>${descBlock}</div>`
}

export default function LeafletGeoMap({ points, polygons, height = 420 }: LeafletGeoMapProps) {
  const [visibleGroups, setVisibleGroups] = useState<Record<string, boolean>>({})
  const [selectedFeatureId, setSelectedFeatureId] = useState<string | null>(null)
  const [flyToRequest, setFlyToRequest] = useState<FlyToPayload | null>(null)

  const pointCollection = useMemo((): FeatureCollection => {
    return {
      type: 'FeatureCollection',
      features: points.map((point) => ({
        type: 'Feature' as const,
        properties: {
          id: point.id,
          label: point.label ?? '',
          description: point.description ?? '',
          group: point.group ?? 'points',
        },
        geometry: {
          type: 'Point' as const,
          coordinates: point.coordinates,
        },
      })),
    }
  }, [points])

  const polygonCollection = useMemo((): FeatureCollection => {
    return {
      type: 'FeatureCollection',
      features: polygons.map((polygon) => {
        let geometry: Polygon | MultiPolygon
        if (polygon.geometry) {
          geometry = polygon.geometry as Polygon | MultiPolygon
        } else {
          geometry = {
            type: 'Polygon',
            coordinates: [createPolygonCoordinates(polygon.bbox)],
          }
        }
        return {
          type: 'Feature' as const,
          properties: {
            id: polygon.id,
            label: polygon.label ?? '',
            description: polygon.description ?? '',
            group: polygon.group ?? 'areas',
          },
          geometry,
        }
      }),
    }
  }, [polygons])

  const legendGroups: LegendGroup[] = useMemo(() => {
    const entries: LegendGroup[] = []
    const seen = new Set<string>()

    polygons.forEach((polygon) => {
      const group = polygon.group ?? 'areas'
      if (!seen.has(group)) {
        seen.add(group)
        entries.push({ id: group, type: 'polygon', label: group })
      }
    })

    points.forEach((point) => {
      const group = point.group ?? 'points'
      if (!seen.has(group)) {
        seen.add(group)
        entries.push({ id: group, type: 'point', label: group })
      }
    })

    return entries
  }, [points, polygons])

  // Visibility defaults to ON when a group id is absent (matches checkbox `checked={visibleGroups[id] ?? true}`).
  const activeGroups = useMemo(() => {
    return legendGroups.map((g) => g.id).filter((groupId) => visibleGroups[groupId] ?? true)
  }, [visibleGroups, legendGroups])

  const filteredPointCollection = useMemo((): FeatureCollection => {
    if (activeGroups.length === 0) {
      return { type: 'FeatureCollection', features: [] }
    }
    return {
      type: 'FeatureCollection',
      features: pointCollection.features.filter((f) => {
        const g = (f.properties as { group?: string })?.group ?? 'points'
        return activeGroups.includes(g)
      }),
    }
  }, [pointCollection, activeGroups])

  const filteredPolygonCollection = useMemo((): FeatureCollection => {
    if (activeGroups.length === 0) {
      return { type: 'FeatureCollection', features: [] }
    }
    return {
      type: 'FeatureCollection',
      features: polygonCollection.features.filter((f) => {
        const g = (f.properties as { group?: string })?.group ?? 'areas'
        return activeGroups.includes(g)
      }),
    }
  }, [polygonCollection, activeGroups])

  const fitBounds = useMemo(() => getLeafletBounds(points, polygons), [points, polygons])
  const boundsKey = useMemo(
    () => `${points.map((p) => p.id).join(',')}|${polygons.map((p) => p.id).join(',')}`,
    [points, polygons],
  )

  const clearFlyTo = useCallback(() => setFlyToRequest(null), [])

  const handleToggle = (groupId: string) => {
    setVisibleGroups((prev) => ({
      ...prev,
      [groupId]: !(prev[groupId] ?? true),
    }))
  }

  const handleRowClick = (featureId: string, type: 'Point' | 'Polygon') => {
    setSelectedFeatureId((current) => (current === featureId ? null : featureId))
    setFlyToRequest({ id: featureId, type, nonce: Date.now() })
  }

  const featuresForList = useMemo(() => {
    const polygonEntries = polygons.map((polygon) => ({
      id: polygon.id,
      type: 'Polygon' as const,
      label: polygon.label ?? polygon.id,
      description: polygon.description ?? '',
      bbox: polygon.bbox,
    }))

    const pointEntries = points.map((point) => ({
      id: point.id,
      type: 'Point' as const,
      label: point.label ?? point.id,
      description: point.description ?? '',
      coordinates: point.coordinates,
    }))

    return [...polygonEntries, ...pointEntries]
  }, [points, polygons])

  const formatCoordinates = (coords: [number, number] | [number, number, number, number]) => {
    if (coords.length === 2) {
      const [lon, lat] = coords
      return `${lat.toFixed(5)}, ${lon.toFixed(5)}`
    }
    const [west, south, east, north] = coords
    return `${south.toFixed(5)}, ${west.toFixed(5)} — ${north.toFixed(5)}, ${east.toFixed(5)}`
  }

  const onEachPolygon = useCallback(
    (feature: Feature, layer: L.Layer) => {
      const props = feature.properties as { id?: string; label?: string; description?: string } | null
      const id = props?.id
      const title = props?.label || id || 'Location'
      const description = props?.description
      const lg = layer as L.Path
      lg.bindPopup(popupHtml(title, description), { className: 'agate-map-popup' })
      lg.on('click', () => {
        setSelectedFeatureId(id ?? null)
        lg.openPopup()
      })
      lg.on('mouseover', function onOver(this: L.Path) {
        const m = this._map
        if (m) m.getContainer().style.cursor = 'pointer'
      })
      lg.on('mouseout', function onOut(this: L.Path) {
        const m = this._map
        if (m) m.getContainer().style.cursor = ''
      })
    },
    [setSelectedFeatureId],
  )

  const polygonStyleFn = useCallback(
    (feature?: Feature) => {
      const id = (feature?.properties as { id?: string } | undefined)?.id
      const selected = id === selectedFeatureId
      return {
        color: '#1d4ed8',
        weight: selected ? 4 : 2,
        fillColor: '#3b82f6',
        fillOpacity: selected ? 0.35 : 0.2,
      }
    },
    [selectedFeatureId],
  )

  const pointToLayer = useCallback(
    (feature: Feature, latlng: L.LatLng) => {
      const id = (feature.properties as { id?: string } | undefined)?.id
      const selected = id === selectedFeatureId
      return L.circleMarker(latlng, {
        radius: selected ? 8 : 6,
        fillColor: '#ef4444',
        color: '#ffffff',
        weight: 1.5,
        opacity: 1,
        fillOpacity: 1,
      })
    },
    [selectedFeatureId],
  )

  const onEachPoint = useCallback(
    (feature: Feature, layer: L.Layer) => {
      const props = feature.properties as { id?: string; label?: string; description?: string } | null
      const id = props?.id
      const title = props?.label || id || 'Location'
      const description = props?.description
      const marker = layer as L.CircleMarker
      marker.bindPopup(popupHtml(title, description), { className: 'agate-map-popup' })
      marker.on('click', () => {
        setSelectedFeatureId(id ?? null)
        marker.openPopup()
      })
      marker.on('mouseover', function onOver(this: L.CircleMarker) {
        const m = this._map
        if (m) m.getContainer().style.cursor = 'pointer'
      })
      marker.on('mouseout', function onOut(this: L.CircleMarker) {
        const m = this._map
        if (m) m.getContainer().style.cursor = ''
      })
    },
    [setSelectedFeatureId],
  )

  if (points.length === 0 && polygons.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-muted h-[180px] flex items-center justify-center text-sm text-muted-foreground">
        This node did not produce any geocoded features to display.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {legendGroups.length > 0 && (
        <div className="flex flex-wrap gap-2 text-sm">
          {legendGroups.map((group) => {
            const colorClass =
              group.type === 'polygon'
                ? 'bg-blue-100 text-blue-800 border border-blue-200'
                : 'bg-red-100 text-red-800 border border-red-200'
            return (
              <label
                key={group.id}
                className={`inline-flex items-center gap-2 px-3 py-1 rounded-full cursor-pointer select-none ${colorClass}`}
              >
                <input
                  type="checkbox"
                  checked={visibleGroups[group.id] ?? true}
                  onChange={() => handleToggle(group.id)}
                  className="h-4 w-4"
                />
                <span className="capitalize">{group.label}</span>
              </label>
            )
          })}
        </div>
      )}

      <div className="flex flex-col gap-4 md:flex-row">
        <div
          className="rounded-md overflow-hidden border border-border md:w-1/2 w-full z-0 [&_.leaflet-container]:font-sans"
          style={{ height }}
        >
          <MapContainer
            center={DEFAULT_CENTER}
            zoom={3}
            style={{ height: '100%', width: '100%' }}
            scrollWheelZoom
            className="rounded-md"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <FitBoundsOnData bounds={fitBounds} boundsKey={boundsKey} />
            <InvalidateOnResize height={height} />
            <FlyToOnRequest request={flyToRequest} points={points} polygons={polygons} onDone={clearFlyTo} />
            <GeoJSON
              key={`polygons-${selectedFeatureId}-${activeGroups.join(',')}`}
              data={filteredPolygonCollection as GeoJsonObject}
              style={polygonStyleFn as L.StyleFunction}
              onEachFeature={onEachPolygon}
            />
            <GeoJSON
              key={`points-${selectedFeatureId}-${activeGroups.join(',')}`}
              data={filteredPointCollection as GeoJsonObject}
              pointToLayer={pointToLayer}
              onEachFeature={onEachPoint}
            />
          </MapContainer>
        </div>

        <div className="md:w-1/2 w-full rounded-md border border-border bg-card">
          <div className="max-h-[420px] overflow-y-auto divide-y divide-border">
            {featuresForList.map((feature) => (
              <button
                key={feature.id}
                type="button"
                onClick={() => handleRowClick(feature.id, feature.type)}
                className={`w-full text-left p-4 space-y-1 transition-colors ${
                  selectedFeatureId === feature.id ? 'bg-primary/10' : 'hover:bg-muted'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{feature.label}</span>
                  <span className="text-xs uppercase tracking-wide text-muted-foreground">
                    {feature.type}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground font-mono">
                  {feature.type === 'Point'
                    ? formatCoordinates(feature.coordinates)
                    : formatCoordinates(feature.bbox)}
                </div>
                {feature.description && (
                  <div className="text-sm text-muted-foreground">{feature.description}</div>
                )}
              </button>
            ))}
            {featuresForList.length === 0 && (
              <div className="p-4 text-sm text-muted-foreground">No geocoded features available.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
