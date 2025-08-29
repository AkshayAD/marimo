/* Copyright 2024 Marimo. All rights reserved. */
import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import { CellId } from "@/core/cells/ids";
import { generateUUID } from "@/utils/uuid";

export type AgentRole = "user" | "assistant" | "system";
export type SuggestionType = "new_cell" | "modify_cell" | "delete_cell" | "execute_cell";
export type ExecutionStatus = "pending" | "executing" | "complete" | "error" | "cancelled";

export interface CodeSuggestion {
  id: string;
  type: SuggestionType;
  code: string;
  cellId?: CellId;
  position?: "before" | "after" | "replace";
  description?: string;
  autoExecute?: boolean;
}

export interface ExecutionStep {
  stepId: string;
  description: string;
  suggestion?: CodeSuggestion;
  status: ExecutionStatus;
  progress?: number;
  result?: any;
  error?: string;
}

export interface AgentMessage {
  id: string;
  role: AgentRole;
  content: string;
  suggestions?: CodeSuggestion[];
  timestamp: number;
}

export interface AgentConfig {
  enabled: boolean;
  defaultModel: string;
  customModel?: string | null;  // Custom model override
  autoExecute: boolean;
  requireApproval: boolean;
  maxSteps: number;
  streamResponses: boolean;
  maxTokens: number;
  temperature: number;
  safetyMode: "strict" | "balanced" | "permissive";
}

interface AgentState {
  // UI State
  isOpen: boolean;
  width: number;
  isMinimized: boolean;
  
  // Chat State
  messages: AgentMessage[];
  isLoading: boolean;
  streamingMessage: string | null;
  streamingMessageId: string | null;
  
  // Execution State
  currentPlan: ExecutionStep[];
  executingStepId: string | null;
  pendingSuggestions: CodeSuggestion[];
  
  // Configuration
  config: AgentConfig;
  availableModels: string[];
  
  // WebSocket
  wsConnected: boolean;
  wsError: string | null;
  sessionId: string | null;
  lastPingTime: number | null;
  
  // Actions
  toggleOpen: () => void;
  setWidth: (width: number) => void;
  toggleMinimized: () => void;
  
  addMessage: (message: Omit<AgentMessage, "id" | "timestamp">) => void;
  updateMessage: (id: string, updates: Partial<AgentMessage>) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setStreamingMessage: (message: string | null, messageId?: string | null) => void;
  
  setPlan: (plan: ExecutionStep[]) => void;
  updateStepStatus: (stepId: string, status: ExecutionStatus, result?: any, error?: string) => void;
  setExecutingStep: (stepId: string | null) => void;
  addSuggestion: (suggestion: CodeSuggestion) => void;
  removeSuggestion: (id: string) => void;
  clearSuggestions: () => void;
  
  updateConfig: (config: Partial<AgentConfig>) => void;
  setAvailableModels: (models: string[]) => void;
  
  setWsConnected: (connected: boolean) => void;
  setWsError: (error: string | null) => void;
  setSessionId: (sessionId: string | null) => void;
  updatePingTime: () => void;
}

const DEFAULT_CONFIG: AgentConfig = {
  enabled: true,
  defaultModel: "openai/gpt-4o",
  customModel: null,
  autoExecute: false,
  requireApproval: true,
  maxSteps: 10,
  streamResponses: true,
  maxTokens: 4096,
  temperature: 0.7,
  safetyMode: "balanced",
};

export const useAgentStore = create<AgentState>()(
  devtools(
    persist(
      (set) => ({
        // UI State - persisted
        isOpen: false,
        width: 400,
        isMinimized: false,
        
        // Chat State - not persisted
        messages: [],
        isLoading: false,
        streamingMessage: null,
        streamingMessageId: null,
        
        // Execution State - not persisted
        currentPlan: [],
        executingStepId: null,
        pendingSuggestions: [],
        
        // Configuration - persisted
        config: DEFAULT_CONFIG,
        availableModels: [
          "openai/gpt-4o",
          "openai/gpt-4o-mini",
          "openai/gpt-3.5-turbo",
          "anthropic/claude-3-5-sonnet-20241022",
          "anthropic/claude-3-haiku-20240307",
          "google/gemini-1.5-pro",
          "groq/llama-3.1-70b-versatile",
        ],
        
        // WebSocket - not persisted
        wsConnected: false,
        wsError: null,
        sessionId: null,
        lastPingTime: null,
        
        // Actions
        toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),
        setWidth: (width) => set({ width }),
        toggleMinimized: () => set((state) => ({ isMinimized: !state.isMinimized })),
        
        addMessage: (message) => set((state) => ({
          messages: [
            ...state.messages,
            {
              ...message,
              id: generateUUID(),
              timestamp: Date.now(),
            },
          ],
        })),
        
        updateMessage: (id, updates) => set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === id ? { ...msg, ...updates } : msg
          ),
        })),
        
        clearMessages: () => set({ messages: [], streamingMessage: null, streamingMessageId: null }),
        setLoading: (isLoading) => set({ isLoading }),
        setStreamingMessage: (streamingMessage, streamingMessageId = null) => 
          set({ streamingMessage, streamingMessageId }),
        
        setPlan: (currentPlan) => set({ currentPlan }),
        updateStepStatus: (stepId, status, result, error) =>
          set((state) => ({
            currentPlan: state.currentPlan.map((step) =>
              step.stepId === stepId
                ? { ...step, status, result, error }
                : step
            ),
          })),
        setExecutingStep: (executingStepId) => set({ executingStepId }),
        
        addSuggestion: (suggestion) => set((state) => ({
          pendingSuggestions: [...state.pendingSuggestions, suggestion],
        })),
        removeSuggestion: (id) => set((state) => ({
          pendingSuggestions: state.pendingSuggestions.filter((s) => s.id !== id),
        })),
        clearSuggestions: () => set({ pendingSuggestions: [] }),
        
        updateConfig: (config) =>
          set((state) => ({
            config: { ...state.config, ...config },
          })),
        setAvailableModels: (availableModels) => set({ availableModels }),
        
        setWsConnected: (wsConnected) => set({ wsConnected, wsError: wsConnected ? null : undefined }),
        setWsError: (wsError) => set({ wsError }),
        setSessionId: (sessionId) => set({ sessionId }),
        updatePingTime: () => set({ lastPingTime: Date.now() }),
      }),
      {
        name: "marimo-agent-storage",
        partialize: (state) => ({
          isOpen: state.isOpen,
          width: state.width,
          isMinimized: state.isMinimized,
          config: state.config,
        }),
      }
    ),
    {
      name: "AgentStore",
    }
  )
);