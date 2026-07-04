import { create } from 'zustand';

interface ChatStore {
  activeChannel: string;
  setActiveChannel: (channelId: string) => void;
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  activeChannel: 'general',
  setActiveChannel: (channelId) => set({ activeChannel: channelId }),
  isSidebarOpen: true,
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
}));
