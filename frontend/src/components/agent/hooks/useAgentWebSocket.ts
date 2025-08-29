/* Copyright 2024 Marimo. All rights reserved. */
import { useEffect, useRef, useCallback } from "react";
import { useAgentStore } from "../stores/agent-state";
// import { API } from "@/core/network/api";
// import { getCellsAsJSON } from "@/core/cells/cells";
// import { getNotebook } from "@/core/cells/cells";
import { variablesAtom } from "@/core/variables/state";
import { useAtomValue } from "jotai";

export const useAgentWebSocket = () => {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const pingInterval = useRef<NodeJS.Timeout | null>(null);
  
  const {
    config,
    setWsConnected,
    setWsError,
    setSessionId,
    addMessage,
    updateMessage,
    setStreamingMessage,
    setLoading,
    setPlan,
    updateStepStatus,
    updatePingTime,
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
      setWsError(null);
      
      // Initialize session
      ws.current?.send(
        JSON.stringify({
          type: "init",
          config: useAgentStore.getState().config,
        })
      );
      
      // Start ping interval
      pingInterval.current = setInterval(() => {
        if (ws.current?.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ type: "ping" }));
          updatePingTime();
        }
      }, 30000); // Ping every 30 seconds
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
      setWsError("Connection error");
    };

    ws.current.onclose = (event) => {
      console.log("Agent WebSocket disconnected:", event.code, event.reason);
      setWsConnected(false);
      ws.current = null;
      
      if (pingInterval.current) {
        clearInterval(pingInterval.current);
        pingInterval.current = null;
      }
      
      // Auto-reconnect unless it was a clean close
      if (event.code !== 1000) {
        setWsError(`Connection closed: ${event.reason || 'Unknown reason'}`);
        reconnectTimeout.current = setTimeout(() => {
          connect();
        }, 3000);
      }
    };
  }, [setWsConnected, setSessionId]);

  const handleMessage = useCallback(
    (data: any) => {
      switch (data.type) {
        case "init_complete":
          setSessionId(data.session_id);
          break;
          
        case "stream_chunk":
          setStreamingMessage(data.accumulated, data.message_id);
          break;
          
        case "stream_complete":
          // Finalize the streaming message
          if (data.message_id) {
            updateMessage(data.message_id, {
              content: data.final_message,
            });
          } else {
            addMessage({
              role: "assistant",
              content: data.final_message,
            });
          }
          setStreamingMessage(null);
          setLoading(false);
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
          
        case "execution_result":
          if (data.result?.status === "success") {
            updateStepStatus(data.step_id, "complete", data.result);
          } else {
            updateStepStatus(data.step_id, "error", null, data.result?.error);
          }
          break;
          
        case "error":
          setLoading(false);
          setStreamingMessage(null);
          setWsError(data.message);
          addMessage({
            role: "assistant",
            content: `Error: ${data.message}`,
          });
          break;
          
        case "cleared":
          // Memory cleared successfully
          break;
          
        case "pong":
          updatePingTime();
          break;
      }
    },
    [
      setSessionId,
      setLoading,
      setStreamingMessage,
      updateMessage,
      addMessage,
      setPlan,
      updateStepStatus,
      setWsError,
      updatePingTime,
    ]
  );

  const sendMessage = useCallback(
    async (message: string) => {
      if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
        throw new Error("WebSocket not connected");
      }

      // Get current notebook context
      // TODO: Import these functions from core when available
      // For now, we'll try to get them if they exist
      let cells: any[] = [];
      let activeCellId = null;
      
      try {
        // Try to access cells from window or global context
        // This would need to be properly imported from @/core/cells/cells
        if (typeof window !== 'undefined' && (window as any).marimoGetCells) {
          cells = (window as any).marimoGetCells();
        }
        if (typeof window !== 'undefined' && (window as any).marimoGetActiveCell) {
          activeCellId = (window as any).marimoGetActiveCell();
        }
      } catch (e) {
        // Context not available yet
        console.debug("Notebook context not available");
      }
      
      // Get active model (custom if set, otherwise default)
      const config = useAgentStore.getState().config;
      const activeModel = config.customModel || config.defaultModel;
      
      // Build context
      const context = {
        active_cell_id: activeCellId,
        cell_codes: Object.fromEntries(
          cells.map((cell) => [cell.id, cell.code])
        ),
        variables: variables ? Object.fromEntries(
          Object.entries(variables).map(([k, v]) => [k, v])
        ) : {},
        recent_errors: [], // TODO: Track recent errors
        execution_history: [], // TODO: Track execution history
      };

      // Add user message immediately
      addMessage({
        role: "user",
        content: message,
      });
      
      // Set loading and streaming states
      setLoading(true);
      if (config.streamResponses) {
        setStreamingMessage("");
      }
      
      ws.current.send(
        JSON.stringify({
          type: "chat",
          message,
          context,
          model: activeModel,
          stream: config.streamResponses,
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
  
  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    
    if (pingInterval.current) {
      clearInterval(pingInterval.current);
      pingInterval.current = null;
    }
    
    if (ws.current) {
      ws.current.close(1000, "Manual disconnect");
      ws.current = null;
    }
    
    setWsConnected(false);
  }, [setWsConnected]);

  return {
    sendMessage,
    executeSuggestion,
    clearMemory,
    connect,
    disconnect,
  };
};