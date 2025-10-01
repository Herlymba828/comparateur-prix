import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function AnalysesScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Analyses</Text>
      <Text>À implémenter: listing d’analyses et détails.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  title: { fontSize: 20, fontWeight: '600', marginBottom: 8 },
});


