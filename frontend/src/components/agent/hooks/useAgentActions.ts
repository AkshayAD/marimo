/* Copyright 2024 Marimo. All rights reserved. */
import { useCallback } from "react";
import { CodeSuggestion } from "../stores/agent-state";
import { useAgentWebSocket } from "./useAgentWebSocket";
import { createCell, updateCellCode, deleteCell } from "@/core/cells/cells";
import { sendRun } from "@/core/network/requests";
import { CellId } from "@/core/cells/ids";

export const useAgentActions = () => {
  const { executeSuggestion } = useAgentWebSocket();

  const applySuggestion = useCallback(
    async (suggestion: CodeSuggestion) => {
      switch (suggestion.type) {
        case "new_cell": {
          // Create new cell
          const cellId = createCell({
            code: suggestion.code,
            before: suggestion.position === "before" ? suggestion.cellId : undefined,
            after: suggestion.position === "after" ? suggestion.cellId : undefined,
          });
          
          // Execute if auto-execute is enabled
          if (suggestion.autoExecute && cellId) {
            await sendRun([cellId]);
          }
          
          return cellId;
        }
        
        case "modify_cell": {
          if (!suggestion.cellId) {
            throw new Error("Cell ID required for modification");
          }
          
          // Update cell code
          updateCellCode({
            cellId: suggestion.cellId as CellId,
            code: suggestion.code,
          });
          
          // Execute if auto-execute is enabled
          if (suggestion.autoExecute) {
            await sendRun([suggestion.cellId as CellId]);
          }
          
          return suggestion.cellId;
        }
        
        case "delete_cell": {
          if (!suggestion.cellId) {
            throw new Error("Cell ID required for deletion");
          }
          
          // Delete cell
          deleteCell(suggestion.cellId as CellId);
          
          return suggestion.cellId;
        }
        
        case "execute_cell": {
          if (!suggestion.cellId) {
            throw new Error("Cell ID required for execution");
          }
          
          // Execute cell
          await sendRun([suggestion.cellId as CellId]);
          
          return suggestion.cellId;
        }
        
        default:
          throw new Error(`Unknown suggestion type: ${suggestion.type}`);
      }
    },
    []
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