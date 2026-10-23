import { get, post } from './client';
import type { AuthConfig, Me } from './types';

export const fetchMe = (signal?: AbortSignal) => get<Me>('/me', signal);
export const fetchAuthConfig = (signal?: AbortSignal) => get<AuthConfig>('/auth/config', signal);
export const logout = () => post<undefined>('/auth/logout');
export const DISCORD_LOGIN_URL = '/api/v1/auth/discord/login';
export const demoLoginUrl = (admin: boolean) => `/api/v1/auth/demo${admin ? '?admin=true' : ''}`;
