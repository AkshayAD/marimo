/* Copyright 2024 Marimo. All rights reserved. */
import { useEffect, useRef, useCallback } from "react";
import { useAgentStore } from "../stores/agent-state";
import { API } from "@/core/network/api";
import { getCellsAsJSON } from "@/core/cells/cells";
import { getNotebook } from "@/core/cells/cells";
import { variablesAtom } from "@/core/variables/state";
import { useAtomValue } from "jotai";

export const useAgentWebSocket = () => {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  
  const {
    setWsConnected,
    setSessionId,
    addMessage,
    setStreamingMessage,
    setLoading,
    setPlan,
    updateStepStatus,
  } = useAgentStore();

  const variables = useAtomValue(variablesAtom);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const url = `${protocol}//${host}/api/agent/stream`;

    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      console.log("Agent WebSocket connected");
      setWsConnected(true);
      
      // Initialize session
      ws.current?.send(
        JSON.stringify({
          type: "init",
          config: useAgentStore.getState().config,
        })
      );
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleMessage(data);
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    ws.current.onerror = (error) => {
      console.error("Agent WebSocket error:", error);
    };

    ws.current.onclose = () => {
      console.log("Agent WebSocket disconnected");
      setWsConnected(false);
      ws.current = null;
      
      // Attempt to reconnect after 3 seconds
      reconnectTimeout.current = setTimeout(() => {
        connect();
      }, 3000);
    };
  }, [setWsConnected, setSessionId]);

  const handleMessage = useCallback(
    (data: any) => {
      switch (data.type) {
        case "init_complete":
          setSessionId(data.session_id);
          break;
          
        case "response":
          setLoading(false);
          setStreamingMessage(null);
          addMessage({
            role: "assistant",
            content: data.message,
            suggestions: data.suggestions,
          });
          if (data.execution_plan) {
            setPlan(data.execution_plan);
          }
          break;
          
        case "streaming":
          setStreamingMessage(data.content);
          break;
          
        case "execution_result":
          if (data.result.status === "success") {
            updateStepStatus(data.step_id, "complete", data.result);
          } else {
            updateStepStatus(data.step_id, "error", null, data.result.error);
          }
          break;
          
        case "error":
          setLoading(false);
          setStreamingMessage(null);
          addMessage({
            role: "assistant",
            content: `Error: ${data.message}`,
          });
          break;
          
        case "cleared":
          // Memory cleared successfully
          break;
      }
    },
    [
      setSessionId,
      setLoading,
      setStreamingMessage,
      addMessage,
      setPlan,
      updateStepStatus,
    ]
  );

  const sendMessage = useCallback(
    async (message: string) => {
      if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
        throw new Error("WebSocket not connected");
      }

      // Get current notebook context
      const cells = getCellsAsJSON();
      const notebook = getNotebook();
      const activeCellId = notebook.activeCell;
      
      // Build context
      const context = {
        active_cell_id: activeCellId,
        cell_codes: Object.fromEntries(
          cells.map((cell) => [cell.id, cell.code])
        ),
        variables: Object.fromEntries(
          variables.map((v) => [v.name, v.value])
        ),
        recent_errors: [], // TODO: Track recent errors
        execution_history: [], // TODO: Track execution history
      };

      ws.current.send(
        JSON.stringify({
          type: "chat",
          message,
          context,
        })
      );
    },
    [variables]
  );

  const executeSuggestion = useCallback(
    async (suggestion: any) => {
      if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
        throw new Error("WebSocket not connected");
      }

      ws.current.send(
        JSON.stringify({
          type: "execute",
          suggestion,
        })
      );
    },
    []
  );

  const clearMemory = useCallback(() => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      return;
    }

    ws.current.send(
      JSON.stringify({
        type: "clear",
      })
    );
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  return {
    sendMessage,
    executeSuggestion,
    clearMemory,
  };
};