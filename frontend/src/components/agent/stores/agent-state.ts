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
  
  // Execution State
  currentPlan: ExecutionStep[];
  executingStepId: string | null;
  
  // Configuration
  config: AgentConfig;
  
  // WebSocket
  wsConnected: boolean;
  sessionId: string | null;
  
  // Actions
  toggleOpen: () => void;
  setWidth: (width: number) => void;
  toggleMinimized: () => void;
  
  addMessage: (message: Omit<AgentMessage, "id" | "timestamp">) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setStreamingMessage: (message: string | null) => void;
  
  setPlan: (plan: ExecutionStep[]) => void;
  updateStepStatus: (stepId: string, status: ExecutionStatus, result?: any, error?: string) => void;
  setExecutingStep: (stepId: string | null) => void;
  
  updateConfig: (config: Partial<AgentConfig>) => void;
  
  setWsConnected: (connected: boolean) => void;
  setSessionId: (sessionId: string | null) => void;
}

const DEFAULT_CONFIG: AgentConfig = {
  enabled: true,
  defaultModel: "google/gemini-2.0-flash-exp",
  customModel: null,
  autoExecute: false,
  requireApproval: true,
  maxSteps: 10,
  streamResponses: true,
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
        
        // Execution State - not persisted
        currentPlan: [],
        executingStepId: null,
        
        // Configuration - persisted
        config: DEFAULT_CONFIG,
        
        // WebSocket - not persisted
        wsConnected: false,
        sessionId: null,
        
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
        
        clearMessages: () => set({ messages: [] }),
        setLoading: (isLoading) => set({ isLoading }),
        setStreamingMessage: (streamingMessage) => set({ streamingMessage }),
        
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
        
        updateConfig: (config) =>
          set((state) => ({
            config: { ...state.config, ...config },
          })),
        
        setWsConnected: (wsConnected) => set({ wsConnected }),
        setSessionId: (sessionId) => set({ sessionId }),
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