/* Copyright 2024 Marimo. All rights reserved. */
import React, { useState } from "react";
import { CodeSuggestion } from "./stores/agent-state";
import { Button } from "@/components/ui/button";
import { cn } from "@/utils/cn";
import {
  Check,
  X,
  Play,
  FileText,
  Edit,
  Trash,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { CodeMirror } from "@/components/editor/codemirror/CodeMirror";
import { python } from "@codemirror/lang-python";
import { useAgentActions } from "./hooks/useAgentActions";

interface AgentSuggestionProps {
  suggestion: CodeSuggestion;
}

export const AgentSuggestion: React.FC<AgentSuggestionProps> = ({
  suggestion,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isApplied, setIsApplied] = useState(false);
  const { applySuggestion } = useAgentActions();

  const getIcon = () => {
    switch (suggestion.type) {
      case "new_cell":
        return <FileText className="h-4 w-4" />;
      case "modify_cell":
        return <Edit className="h-4 w-4" />;
      case "delete_cell":
        return <Trash className="h-4 w-4" />;
      case "execute_cell":
        return <Play className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getTitle = () => {
    switch (suggestion.type) {
      case "new_cell":
        return "New Cell";
      case "modify_cell":
        return "Modify Cell";
      case "delete_cell":
        return "Delete Cell";
      case "execute_cell":
        return "Execute Cell";
      default:
        return "Suggestion";
    }
  };

  const handleApply = async () => {
    try {
      await applySuggestion(suggestion);
      setIsApplied(true);
    } catch (error) {
      console.error("Failed to apply suggestion:", error);
    }
  };

  return (
    <div
      className={cn(
        "border rounded-lg overflow-hidden",
        isApplied && "opacity-60"
      )}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between p-2 bg-muted/30 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <button className="hover:bg-muted rounded p-0.5">
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </button>
          {getIcon()}
          <span className="text-sm font-medium">{getTitle()}</span>
          {suggestion.description && (
            <span className="text-xs text-muted-foreground">
              - {suggestion.description}
            </span>
          )}
        </div>
        
        {!isApplied && (
          <div className="flex items-center gap-1">
            <Button
              size="sm"
              variant="ghost"
              className="h-6 px-2"
              onClick={(e) => {
                e.stopPropagation();
                handleApply();
              }}
              title="Apply suggestion"
            >
              <Check className="h-3 w-3 mr-1" />
              Apply
            </Button>
          </div>
        )}
        
        {isApplied && (
          <span className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
            <Check className="h-3 w-3" />
            Applied
          </span>
        )}
      </div>

      {/* Code */}
      {isExpanded && suggestion.code && (
        <div className="p-2 border-t">
          <div className="rounded border bg-background overflow-hidden">
            <CodeMirror
              value={suggestion.code}
              extensions={[python()]}
              editable={false}
              className="text-xs"
              height="auto"
              maxHeight="200px"
            />
          </div>
          
          {/* Additional Info */}
          <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
            {suggestion.cellId && (
              <span>Target: Cell {suggestion.cellId.slice(0, 8)}</span>
            )}
            {suggestion.position && (
              <span>Position: {suggestion.position}</span>
            )}
            {suggestion.autoExecute && (
              <span className="text-orange-600 dark:text-orange-400">
                Auto-execute enabled
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};