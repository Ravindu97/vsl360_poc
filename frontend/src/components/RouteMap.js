import React, { useEffect, useState } from 'react';
import { Box, Typography, Card, CardContent, Chip } from '@mui/material';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});



const RouteMap = ({ cityCoordinates, routeDistances }) => {
  const [routeSegments, setRouteSegments] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (cityCoordinates && cityCoordinates.length > 1) {
      fetchRouteSegments();
    }
  }, [cityCoordinates]);

  const fetchRouteSegments = async () => {
    setLoading(true);
    const segments = [];
    
    for (let i = 0; i < cityCoordinates.length - 1; i++) {
      const from = cityCoordinates[i];
      const to = cityCoordinates[i + 1];
      
      try {
        // Using OSRM (Open Source Routing Machine) - free service
        const response = await fetch(
          `https://router.project-osrm.org/route/v1/driving/${from.lng},${from.lat};${to.lng},${to.lat}?overview=full&geometries=geojson`
        );
        
        if (response.ok) {
          const data = await response.json();
          if (data.routes && data.routes.length > 0) {
            const route = data.routes[0];
            const coordinates = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);
            
            segments.push({
              coordinates,
              distance: routeDistances?.[i]?.distance_km ? `${routeDistances[i].distance_km} km` : 'N/A',
              from: from.city,
              to: to.city
            });
          } else {
            throw new Error('No route found');
          }
        } else {
          throw new Error('Routing service unavailable');
        }
      } catch (error) {
        console.log(`Routing failed for ${from.city} to ${to.city}, using straight line`);
        // Fallback to straight line with backend distance
        segments.push({
          coordinates: [[from.lat, from.lng], [to.lat, to.lng]],
          distance: routeDistances?.[i]?.distance_km ? `${routeDistances[i].distance_km} km` : 'N/A',
          from: from.city,
          to: to.city
        });
      }
      
      // Add small delay to be respectful to free service
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    setRouteSegments(segments);
    setLoading(false);
  };

  if (!cityCoordinates || cityCoordinates.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography>No coordinates available for map display</Typography>
      </Box>
    );
  }

  // Calculate center point for the map
  const centerLat = cityCoordinates.reduce((sum, coord) => sum + coord.lat, 0) / cityCoordinates.length;
  const centerLng = cityCoordinates.reduce((sum, coord) => sum + coord.lng, 0) / cityCoordinates.length;

  return (
    <Card sx={{ 
      mb: 2,
      border: '2px solid',
      borderColor: '#87ceeb',
      transition: 'all 0.3s ease',
      '&:hover': {
        borderColor: '#1976d2',
        boxShadow: '0 4px 12px rgba(135, 206, 235, 0.3)'
      }
    }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 2 }}>Travel Route Map</Typography>
        {loading && (
          <Typography variant="body2" color="primary" sx={{ mb: 1 }}>
            Loading real road routes...
          </Typography>
        )}
        <Box sx={{ height: '400px', width: '100%', mb: 2 }}>
          <MapContainer 
            center={[centerLat, centerLng]} 
            zoom={6} 
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {cityCoordinates.map((coord, index) => {
              const isStart = index === 0;
              const isEnd = index === cityCoordinates.length - 1;
              let label = `${index + 1}. ${coord.city}`;
              
              if (isStart) {
                label = `🚀 START: ${coord.city}`;
              } else if (isEnd) {
                label = `🏁 END: ${coord.city}`;
              }
              
              return (
                <Marker key={coord.city} position={[coord.lat, coord.lng]}>
                  <Popup>
                    <strong style={{ color: isStart ? 'green' : isEnd ? 'red' : 'blue' }}>{label}</strong><br />
                    Coordinates: {coord.lat.toFixed(4)}, {coord.lng.toFixed(4)}
                  </Popup>
                </Marker>
              );
            })}}
            {routeSegments.map((segment, index) => (
              <Polyline 
                key={`route-${index}`}
                positions={segment.coordinates} 
                color="red" 
                weight={4}
                opacity={0.8}
              >
                <Popup>
                  <strong>{segment.from} → {segment.to}</strong><br />
                  Distance: {segment.distance}
                </Popup>
              </Polyline>
            ))}
          </MapContainer>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Red lines show real road routes with distances. Click on routes or markers for details.
        </Typography>
        {routeSegments.length > 0 && (
          <Box sx={{ 
            mt: 2, 
            p: 2, 
            bgcolor: 'success.50', 
            borderRadius: 2, 
            border: '2px solid', 
            borderColor: 'success.main',
            textAlign: 'center'
          }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'success.main' }}>
              🛣️ Total Trip Distance: {routeDistances.reduce((sum, route) => sum + parseFloat(route.distance_km || 0), 0).toFixed(1)} km
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default RouteMap;