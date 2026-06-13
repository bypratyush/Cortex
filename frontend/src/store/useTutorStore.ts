import { create } from 'zustand';

interface TutorContext {
  conceptId?: string | null;
  lessonId?: string | null;
  quizId?: string | null;
  contextPill?: string | null;
}

interface TutorStore {
  isOpen: boolean;
  context: TutorContext | null;
  conversationId: string | null;
  openTutor: (ctx: TutorContext) => void;
  closeTutor: () => void;
  setConversationId: (id: string | null) => void;
}

export const useTutorStore = create<TutorStore>((set) => ({
  isOpen: false,
  context: null,
  conversationId: null,
  
  openTutor: (ctx) => set({ isOpen: true, context: ctx }),
  closeTutor: () => set({ isOpen: false, context: null, conversationId: null }),
  setConversationId: (id) => set({ conversationId: id }),
}));
