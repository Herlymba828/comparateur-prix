import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import MapView, { Marker } from 'react-native-maps';
import * as Location from 'expo-location';
import { api } from '../services/api';

export default function StoresScreen() {
  const [region, setRegion] = useState<any>(null);
  const [stores, setStores] = useState<any[]>([]);

  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === 'granted') {
        const loc = await Location.getCurrentPositionAsync({});
        setRegion({
          latitude: loc.coords.latitude,
          longitude: loc.coords.longitude,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        });
      } else {
        setRegion({ latitude: 0.39, longitude: 9.45, latitudeDelta: 0.5, longitudeDelta: 0.5 }); // Gabon approx
      }
      const res = await api.get('/api/magasins/magasins/');
      setStores(res.data?.results || res.data || []);
    })();
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Magasins</Text>
      {region && (
        <MapView style={styles.map} initialRegion={region}>
          {stores.filter(s => s.latitude && s.longitude).map((s, i) => (
            <Marker key={String(s.id || i)} coordinate={{ latitude: s.latitude, longitude: s.longitude }} title={s.nom} />
          ))}
        </MapView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  title: { fontSize: 18, fontWeight: '600', padding: 16 },
  map: { width: Dimensions.get('window').width, height: Dimensions.get('window').height - 100 },
});


