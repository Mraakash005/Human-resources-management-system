'use client';

import { useEffect } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';
import { setAccessToken } from '@/lib/api';

export function useAuthSync() {
  const { getToken } = useAuth();
  const { user, isLoaded } = useUser();

  useEffect(() => {
    let mounted = true;

    async function syncToken() {
      try {
        const token = await getToken();
        if (mounted) {
          setAccessToken(token);
        }
      } catch {
        if (mounted) {
          setAccessToken(null);
        }
      }
    }

    if (isLoaded) {
      syncToken();
      const interval = setInterval(syncToken, 4 * 60 * 1000);
      return () => {
        mounted = false;
        clearInterval(interval);
      };
    }

    return () => {
      mounted = false;
    };
  }, [getToken, isLoaded]);

  const role = (user?.publicMetadata?.role as string) || 'employee';

  return {
    user,
    isLoaded,
    role,
    isAdmin: role === 'admin',
    userId: user?.id,
  };
}
