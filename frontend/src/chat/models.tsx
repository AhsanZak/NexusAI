import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { loadChatModels, saveChatModel, type ChatModelOption } from "../api/chat";

interface ChatModelState {
  models: ChatModelOption[];
  modelId: string;
  choose: (modelId: string) => Promise<void>;
  refresh: () => Promise<void>;
}

const ChatModelContext = createContext<ChatModelState | null>(null);

export function ChatModelProvider({ children }: { children: ReactNode }) {
  const [models, setModels] = useState<ChatModelOption[]>([]);
  const [modelId, setModelId] = useState("smart-ollama");

  const refresh = useCallback(async () => {
    const loaded = await loadChatModels();
    setModels(loaded.models);
    setModelId(loaded.selected);
  }, []);

  useEffect(() => {
    void refresh().catch(() => undefined);
  }, [refresh]);

  const choose = useCallback(async (next: string) => {
    const saved = await saveChatModel(next);
    setModels(saved.models);
    setModelId(saved.selected);
  }, []);

  const value = useMemo(
    () => ({ models, modelId, choose, refresh }),
    [models, modelId, choose, refresh],
  );
  return <ChatModelContext.Provider value={value}>{children}</ChatModelContext.Provider>;
}

export function useChatModel(): ChatModelState {
  const value = useContext(ChatModelContext);
  if (!value) {
    throw new Error("Chat model choice is only available after sign-in");
  }
  return value;
}
