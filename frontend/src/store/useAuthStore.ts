import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  userId: string | null;
  userEmail: string | null;
  userName: string | null;
  setAuth: (id: string, email: string, name: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      userId: null,
      userEmail: null,
      userName: null,
      setAuth: (id, email, name) => set({ userId: id, userEmail: email, userName: name }),
      logout: () => set({ userId: null, userEmail: null, userName: null }),
    }),
    {
      name: 'cortex-auth-storage', // saves to localStorage
    }
  )
);
