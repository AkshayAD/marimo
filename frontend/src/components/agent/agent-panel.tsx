/* Copyright 2024 Marimo. All rights reserved. */
import React, { useEffect, useRef, useState } from "react";
import { cn } from "@/utils/cn";
import { useAgentStore } from "./stores/agent-state";
import { AgentChat } from "./agent-chat";
import { AgentControls } from "./agent-controls";
import { AgentProgress } from "./agent-progress";
import { Button } from "@/components/ui/button";
import { 
  ChevronRight, 
  ChevronLeft, 
  Bot, 
  Minimize2,
  Maximize2,
  X
} from "lucide-react";
import { useResizable } from "@/hooks/useResizable";
import "./agent-panel.css";

const MIN_WIDTH = 300;
const MAX_WIDTH = 600;
const DEFAULT_WIDTH = 400;

export const AgentPanel: React.FC = () => {
  const {
    isOpen,
    width,
    isMinimized,
    toggleOpen,
    setWidth,
    toggleMinimized,
    wsConnected,
  } = useAgentStore();

  const panelRef = useRef<HTMLDivElement>(null);
  const [isResizing, setIsResizing] = useState(false);

  // Handle resizing
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = window.innerWidth - e.clientX;
      setWidth(Math.min(Math.max(newWidth, MIN_WIDTH), MAX_WIDTH));
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing, setWidth]);

  // Apply body class when panel is open
  useEffect(() => {
    if (isOpen && !isMinimized) {
      document.body.style.setProperty("--agent-panel-width", `${width}px`);
      document.body.classList.add("agent-panel-open");
    } else {
      document.body.classList.remove("agent-panel-open");
    }

    return () => {
      document.body.classList.remove("agent-panel-open");
    };
  }, [isOpen, isMinimized, width]);

  if (!isOpen) {
    return (
      <Button
        variant="ghost"
        size="icon"
        className="fixed right-4 bottom-4 z-50 bg-background shadow-lg border"
        onClick={toggleOpen}
        title="Open AI Agent"
      >
        <Bot className="h-5 w-5" />
      </Button>
    );
  }

  return (
    <aside
      ref={panelRef}
      className={cn(
        "fixed right-0 top-0 h-full bg-background border-l shadow-lg z-40 flex flex-col transition-all duration-300",
        isMinimized ? "w-12" : ""
      )}
      style={{ width: isMinimized ? "48px" : `${width}px` }}
    >
      {/* Resize Handle */}
      {!isMinimized && (
        <div
          className="absolute left-0 top-0 h-full w-1 cursor-ew-resize hover:bg-primary/20 transition-colors"
          onMouseDown={handleMouseDown}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between p-2 border-b shrink-0">
        {!isMinimized && (
          <>
            <div className="flex items-center gap-2">
              <Bot className="h-4 w-4" />
              <span className="font-semibold text-sm">AI Agent</span>
              {!wsConnected && (
                <span className="text-xs text-muted-foreground">(Offline)</span>
              )}
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={toggleMinimized}
                title="Minimize"
              >
                <Minimize2 className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={toggleOpen}
                title="Close"
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          </>
        )}
        {isMinimized && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 mx-auto"
            onClick={toggleMinimized}
            title="Expand"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Content */}
      {!isMinimized && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Chat Area */}
          <div className="flex-1 overflow-hidden">
            <AgentChat />
          </div>

          {/* Execution Progress */}
          <AgentProgress />

          {/* Controls */}
          <div className="border-t p-2 shrink-0">
            <AgentControls />
          </div>
        </div>
      )}
    </aside>
  );
};