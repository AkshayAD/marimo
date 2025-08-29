/* Copyright 2024 Marimo. All rights reserved. */
import React, { useEffect, useRef, useState } from "react";
import { useAgentStore } from "./stores/agent-state";
import { AgentSuggestion } from "./agent-suggestions";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/utils/cn";
import { 
  Send, 
  Loader2, 
  User, 
  Bot,
  RotateCcw
} from "lucide-react";
import { useAgentWebSocket } from "./hooks/useAgentWebSocket";
import { MarkdownRenderer } from "@/plugins/impl/markdown/MarkdownRenderer";

export const AgentChat: React.FC = () => {
  const {
    messages,
    isLoading,
    streamingMessage,
    addMessage,
    clearMessages,
    setLoading,
  } = useAgentStore();

  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { sendMessage } = useAgentWebSocket();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingMessage]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const message = input.trim();
    setInput("");
    
    // Add user message
    addMessage({
      role: "user",
      content: message,
    });

    // Send to agent
    setLoading(true);
    try {
      await sendMessage(message);
    } catch (error) {
      console.error("Failed to send message:", error);
      addMessage({
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        {messages.length === 0 && !streamingMessage && (
          <div className="text-center text-muted-foreground py-8">
            <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-sm">Start a conversation with the AI agent</p>
            <p className="text-xs mt-2">
              I can help you write code, analyze data, and debug issues
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "mb-4 flex gap-3",
              message.role === "user" ? "flex-row-reverse" : ""
            )}
          >
            <div
              className={cn(
                "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
                message.role === "user" 
                  ? "bg-primary text-primary-foreground" 
                  : "bg-muted"
              )}
            >
              {message.role === "user" ? (
                <User className="h-4 w-4" />
              ) : (
                <Bot className="h-4 w-4" />
              )}
            </div>
            
            <div
              className={cn(
                "flex-1 rounded-lg p-3",
                message.role === "user"
                  ? "bg-primary/10 text-right"
                  : "bg-muted/50"
              )}
            >
              <MarkdownRenderer markdown={message.content} />
              
              {/* Suggestions */}
              {message.suggestions && message.suggestions.length > 0 && (
                <div className="mt-3 space-y-2">
                  {message.suggestions.map((suggestion) => (
                    <AgentSuggestion
                      key={suggestion.id}
                      suggestion={suggestion}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Streaming message */}
        {streamingMessage && (
          <div className="mb-4 flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
              <Bot className="h-4 w-4" />
            </div>
            <div className="flex-1 rounded-lg p-3 bg-muted/50">
              <MarkdownRenderer markdown={streamingMessage} />
              <Loader2 className="h-3 w-3 animate-spin mt-2" />
            </div>
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && !streamingMessage && (
          <div className="mb-4 flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
              <Bot className="h-4 w-4" />
            </div>
            <div className="flex-1 rounded-lg p-3 bg-muted/50">
              <div className="flex items-center gap-2">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span className="text-sm text-muted-foreground">
                  Thinking...
                </span>
              </div>
            </div>
          </div>
        )}
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t p-3">
        <div className="flex gap-2">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me to help with your code..."
            className="min-h-[60px] max-h-[120px] resize-none"
            disabled={isLoading}
          />
          <div className="flex flex-col gap-2">
            <Button
              size="icon"
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              title="Send message"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
            {messages.length > 0 && (
              <Button
                size="icon"
                variant="outline"
                onClick={clearMessages}
                title="Clear conversation"
              >
                <RotateCcw className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};