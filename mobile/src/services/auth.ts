import * as SecureStore from 'expo-secure-store';

const ACCESS_KEY = 'auth_access_token';
const REFRESH_KEY = 'auth_refresh_token';

export async function saveTokenPair(tokens: { access?: string; refresh?: string }) {
  if (tokens.access) await SecureStore.setItemAsync(ACCESS_KEY, tokens.access);
  if (tokens.refresh) await SecureStore.setItemAsync(REFRESH_KEY, tokens.refresh);
}

export async function getAccessToken() {
  return SecureStore.getItemAsync(ACCESS_KEY);
}

export async function clearTokens() {
  await SecureStore.deleteItemAsync(ACCESS_KEY);
  await SecureStore.deleteItemAsync(REFRESH_KEY);
}


