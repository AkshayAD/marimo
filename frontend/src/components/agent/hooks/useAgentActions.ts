/* Copyright 2024 Marimo. All rights reserved. */
import { useCallback } from "react";
import type { CodeSuggestion } from "../stores/agent-state";
import { useAgentWebSocket } from "./useAgentWebSocket";
import { useCellActions } from "@/core/cells/cells";
import { useRequestClient } from "@/core/network/requests";
import { CellId } from "@/core/cells/ids";

export const useAgentActions = () => {
  const { executeSuggestion } = useAgentWebSocket();
  const actions = useCellActions();
  const client = useRequestClient();

  const applySuggestion = useCallback(
    async (suggestion: CodeSuggestion) => {
      
      // Implement actual cell operations
      switch (suggestion.type) {
        case "new_cell": {
          // Create new cell
          const position = suggestion.cellId ? 
            (suggestion.position === "before" ? "before" : "after") : 
            "last";
          
          const cellId = actions.createNewCell({
            cellId: suggestion.cellId || "__end__",
            before: position === "before",
            code: suggestion.code,
          });
          
          // Execute if auto-execute is enabled
          if (suggestion.autoExecute && cellId) {
            await client.sendRun({ cellIds: [cellId], codes: [] });
          }
          
          return cellId;
        }
        
        case "modify_cell": {
          if (!suggestion.cellId) {
            throw new Error("Cell ID required for modification");
          }
          
          // Update cell code
          actions.updateCellCode({
            cellId: suggestion.cellId as CellId,
            code: suggestion.code,
            formattingChange: false,
          });
          
          // Execute if auto-execute is enabled
          if (suggestion.autoExecute) {
            await client.sendRun({ cellIds: [suggestion.cellId as CellId], codes: [] });
          }
          
          return suggestion.cellId;
        }
        
        case "delete_cell": {
          if (!suggestion.cellId) {
            throw new Error("Cell ID required for deletion");
          }
          
          // Delete cell
          actions.deleteCell({ cellId: suggestion.cellId as CellId });
          
          return suggestion.cellId;
        }
        
        case "execute_cell": {
          if (!suggestion.cellId) {
            throw new Error("Cell ID required for execution");
          }
          
          // Execute cell
          await client.sendRun({ cellIds: [suggestion.cellId as CellId], codes: [] });
          
          return suggestion.cellId;
        }
        
        default:
          throw new Error(`Unknown suggestion type: ${suggestion.type}`);
      }
    },
    [actions, client]
  );

  const executeRemoteSuggestion = useCallback(
    async (suggestion: CodeSuggestion) => {
      // Execute via WebSocket for more complex operations
      await executeSuggestion(suggestion);
    },
    [executeSuggestion]
  );

  return {
    applySuggestion,
    executeRemoteSuggestion,
  };
};