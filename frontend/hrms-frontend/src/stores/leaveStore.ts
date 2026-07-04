import { create } from 'zustand';

interface LeaveStore {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  selectedLeaveType: string;
  setSelectedLeaveType: (type: string) => void;
  conversationalMessages: Array<{ role: 'user' | 'assistant'; content: string }>;
  addConversationalMessage: (msg: { role: 'user' | 'assistant'; content: string }) => void;
  clearConversationalMessages: () => void;
}

export const useLeaveStore = create<LeaveStore>((set) => ({
  activeTab: 'apply',
  setActiveTab: (tab) => set({ activeTab: tab }),
  selectedLeaveType: 'paid',
  setSelectedLeaveType: (type) => set({ selectedLeaveType: type }),
  conversationalMessages: [
    { role: 'assistant', content: "Hi! Tell me about the leave you need — I'll take care of the rest." }
  ],
  addConversationalMessage: (msg) =>
    set((state) => ({ conversationalMessages: [...state.conversationalMessages, msg] })),
  clearConversationalMessages: () =>
    set({
      conversationalMessages: [
        { role: 'assistant', content: "Hi! Tell me about the leave you need — I'll take care of the rest." }
      ]
    }),
}));
