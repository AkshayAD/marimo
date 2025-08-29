/* Copyright 2024 Marimo. All rights reserved. */
import React from "react";
import { useAgentStore } from "./stores/agent-state";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Settings,
  Zap,
  Shield,
} from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

const AVAILABLE_MODELS = [
  // OpenAI Models (Dec 2024)
  { value: "openai/gpt-4o", label: "GPT-4o (Latest)" },
  { value: "openai/gpt-4o-mini", label: "GPT-4o Mini" },
  { value: "openai/gpt-4-turbo-2024-04-09", label: "GPT-4 Turbo" },
  { value: "openai/gpt-4-1106-preview", label: "GPT-4 (Nov 2023)" },
  { value: "openai/gpt-3.5-turbo-0125", label: "GPT-3.5 Turbo" },
  { value: "openai/o1-preview", label: "o1 Preview (Reasoning)" },
  { value: "openai/o1-mini", label: "o1 Mini" },
  
  // Anthropic Models (Dec 2024)
  { value: "anthropic/claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet (Latest)" },
  { value: "anthropic/claude-3-5-haiku-20241022", label: "Claude 3.5 Haiku" },
  { value: "anthropic/claude-3-opus-20240229", label: "Claude 3 Opus" },
  { value: "anthropic/claude-3-sonnet-20240229", label: "Claude 3 Sonnet" },
  { value: "anthropic/claude-3-haiku-20240307", label: "Claude 3 Haiku" },
  
  // Google Models (Dec 2024)
  { value: "google/gemini-2.0-flash-exp", label: "Gemini 2.0 Flash (Experimental)" },
  { value: "google/gemini-1.5-pro-002", label: "Gemini 1.5 Pro" },
  { value: "google/gemini-1.5-flash-002", label: "Gemini 1.5 Flash" },
  { value: "google/gemini-1.5-flash-8b", label: "Gemini 1.5 Flash 8B" },
  
  // AWS Bedrock Models
  { value: "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0", label: "Bedrock Claude 3.5 Sonnet" },
  { value: "bedrock/anthropic.claude-3-opus-20240229-v1:0", label: "Bedrock Claude 3 Opus" },
  { value: "bedrock/meta.llama3-1-405b-instruct-v1:0", label: "Bedrock Llama 3.1 405B" },
  
  // Custom option
  { value: "custom", label: "Custom Model..." },
];

export const AgentControls: React.FC = () => {
  const { config, updateConfig } = useAgentStore();
  const [showCustomInput, setShowCustomInput] = React.useState(false);
  const [customModelValue, setCustomModelValue] = React.useState(
    config.customModel || ""
  );

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        {/* Auto Execute Toggle */}
        <div className="flex items-center gap-1">
          <Switch
            id="auto-execute"
            checked={config.autoExecute}
            onCheckedChange={(checked) => updateConfig({ autoExecute: checked })}
            className="h-4 w-8"
          />
          <Label
            htmlFor="auto-execute"
            className="text-xs cursor-pointer flex items-center gap-1"
          >
            <Zap className="h-3 w-3" />
            Auto
          </Label>
        </div>

        {/* Require Approval Toggle */}
        <div className="flex items-center gap-1">
          <Switch
            id="require-approval"
            checked={config.requireApproval}
            onCheckedChange={(checked) =>
              updateConfig({ requireApproval: checked })
            }
            className="h-4 w-8"
          />
          <Label
            htmlFor="require-approval"
            className="text-xs cursor-pointer flex items-center gap-1"
          >
            <Shield className="h-3 w-3" />
            Approve
          </Label>
        </div>
      </div>

      {/* Settings Popover */}
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="ghost" size="icon" className="h-6 w-6">
            <Settings className="h-3 w-3" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80" align="end">
          <div className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Agent Settings</h4>
            </div>

            {/* Model Selection */}
            <div className="space-y-2">
              <Label htmlFor="model" className="text-xs">
                Model
              </Label>
              <Select
                value={showCustomInput ? "custom" : config.defaultModel}
                onValueChange={(value) => {
                  if (value === "custom") {
                    setShowCustomInput(true);
                  } else {
                    setShowCustomInput(false);
                    updateConfig({ defaultModel: value, customModel: null });
                  }
                }}
              >
                <SelectTrigger id="model" className="h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AVAILABLE_MODELS.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              {/* Custom Model Input */}
              {showCustomInput && (
                <div className="space-y-2">
                  <Label htmlFor="custom-model" className="text-xs">
                    Custom Model Name
                  </Label>
                  <input
                    id="custom-model"
                    type="text"
                    placeholder="e.g., openai/gpt-4o-2024-12-17"
                    value={customModelValue}
                    onChange={(e) => setCustomModelValue(e.target.value)}
                    onBlur={() => updateConfig({ customModel: customModelValue })}
                    className="w-full h-8 px-2 border rounded text-sm"
                  />
                  <p className="text-xs text-muted-foreground">
                    Enter the exact model identifier for your provider
                  </p>
                </div>
              )}
            </div>

            {/* Max Steps */}
            <div className="space-y-2">
              <Label htmlFor="max-steps" className="text-xs">
                Max Execution Steps
              </Label>
              <input
                id="max-steps"
                type="number"
                min="1"
                max="50"
                value={config.maxSteps}
                onChange={(e) =>
                  updateConfig({ maxSteps: parseInt(e.target.value) || 10 })
                }
                className="w-full h-8 px-2 border rounded text-sm"
              />
            </div>

            {/* Stream Responses */}
            <div className="flex items-center gap-2">
              <Switch
                id="stream-responses"
                checked={config.streamResponses}
                onCheckedChange={(checked) =>
                  updateConfig({ streamResponses: checked })
                }
              />
              <Label htmlFor="stream-responses" className="text-xs">
                Stream Responses
              </Label>
            </div>

            {/* Enable/Disable Agent */}
            <div className="flex items-center gap-2">
              <Switch
                id="agent-enabled"
                checked={config.enabled}
                onCheckedChange={(checked) =>
                  updateConfig({ enabled: checked })
                }
              />
              <Label htmlFor="agent-enabled" className="text-xs">
                Enable Agent
              </Label>
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
};