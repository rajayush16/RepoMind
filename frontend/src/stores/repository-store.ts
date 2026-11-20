import { create } from "zustand";

interface RepositoryState {
  selectedRepositoryId: string | null;
  setSelectedRepositoryId: (id: string | null) => void;
}

export const useRepositoryStore = create<RepositoryState>((set) => ({
  selectedRepositoryId: null,
  setSelectedRepositoryId: (id) => set({ selectedRepositoryId: id }),
}));
