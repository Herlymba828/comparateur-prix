import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TextInput, StyleSheet } from 'react-native';
import { api } from '../services/api';

export default function ProductsScreen() {
  const [q, setQ] = useState('');
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    load();
  }, []);

  async function load() {
    const res = await api.get('/api/produits/api/produits/');
    setItems(res.data?.results || res.data || []);
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Produits</Text>
      <TextInput style={styles.input} placeholder="Rechercher" value={q} onChangeText={setQ} />
      <FlatList data={items} keyExtractor={(it, i) => String(it.id || i)} renderItem={({ item }) => (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>{item.nom}</Text>
          {item.prix_min != null && <Text>Min: {item.prix_min} XAF</Text>}
        </View>
      )} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  title: { fontSize: 20, fontWeight: '600', marginBottom: 8 },
  input: { borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 10, marginBottom: 12 },
  card: { padding: 12, borderWidth: 1, borderColor: '#eee', borderRadius: 10, marginBottom: 10 },
  cardTitle: { fontWeight: '600', marginBottom: 4 },
});


