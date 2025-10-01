import axios from 'axios';
import Constants from 'expo-constants';
import { getAccessToken } from './auth';

const baseURL = (Constants.expoConfig?.extra as any)?.apiBaseUrl || 'http://10.0.2.2:8000';

export const api = axios.create({ baseURL });

api.interceptors.request.use(async config => {
  const token = await getAccessToken();
  if (token) {
    config.headers = config.headers || {};
    (config.headers as any).Authorization = `Bearer ${token}`;
  }
  return config;
});


