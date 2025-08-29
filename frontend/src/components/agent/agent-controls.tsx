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
  // OpenAI Models (Dec 2024 - Verified)
  { value: "openai/gpt-4o", label: "GPT-4o (Multimodal)" },
  { value: "openai/gpt-4o-2024-11-20", label: "GPT-4o Latest" },
  { value: "openai/gpt-4o-mini", label: "GPT-4o Mini (Fast)" },
  { value: "openai/gpt-4o-mini-2024-07-18", label: "GPT-4o Mini Latest" },
  { value: "openai/gpt-4-turbo", label: "GPT-4 Turbo" },
  { value: "openai/gpt-4-turbo-2024-04-09", label: "GPT-4 Turbo April" },
  { value: "openai/gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
  { value: "openai/gpt-3.5-turbo-0125", label: "GPT-3.5 Latest" },
  // O1 reasoning models - Limited availability
  { value: "openai/o1-preview", label: "O1 Preview (Reasoning)" },
  { value: "openai/o1-mini", label: "O1 Mini (Reasoning)" },
  
  // Anthropic Models (Dec 2024 - Confirmed)
  { value: "anthropic/claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet v2" },
  { value: "anthropic/claude-3-5-haiku-20241022", label: "Claude 3.5 Haiku" },
  { value: "anthropic/claude-3-opus-20240229", label: "Claude 3 Opus" },
  { value: "anthropic/claude-3-sonnet-20240229", label: "Claude 3 Sonnet" },
  { value: "anthropic/claude-3-haiku-20240307", label: "Claude 3 Haiku" },
  
  // Google Models (Dec 2024 - Gemini 2.0)
  { value: "google/gemini-2.0-flash-exp", label: "Gemini 2.0 Flash (Exp)" },
  { value: "google/gemini-1.5-pro", label: "Gemini 1.5 Pro" },
  { value: "google/gemini-1.5-pro-002", label: "Gemini 1.5 Pro Latest" },
  { value: "google/gemini-1.5-flash", label: "Gemini 1.5 Flash" },
  { value: "google/gemini-1.5-flash-002", label: "Gemini 1.5 Flash Latest" },
  { value: "google/gemini-1.5-flash-8b", label: "Gemini 1.5 Flash 8B" },
  
  // Groq Models (Fast Inference)
  { value: "groq/llama-3.3-70b-versatile", label: "Llama 3.3 70B" },
  { value: "groq/llama-3.1-70b-versatile", label: "Llama 3.1 70B" },
  { value: "groq/mixtral-8x7b-32768", label: "Mixtral 8x7B" },
  { value: "groq/gemma2-9b-it", label: "Gemma 2 9B" },
  
  // AWS Bedrock Models
  { value: "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0", label: "Bedrock Claude 3.5" },
  { value: "bedrock/anthropic.claude-3-opus-20240229-v1:0", label: "Bedrock Claude Opus" },
  { value: "bedrock/meta.llama3-2-90b-instruct-v1:0", label: "Bedrock Llama 3.2" },
  
  // Custom option - Always last
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
                    Custom Model Identifier
                  </Label>
                  <input
                    id="custom-model"
                    type="text"
                    placeholder="provider/model-name"
                    value={customModelValue}
                    onChange={(e) => setCustomModelValue(e.target.value)}
                    onBlur={() => {
                      if (customModelValue.trim()) {
                        updateConfig({ customModel: customModelValue.trim() });
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && customModelValue.trim()) {
                        updateConfig({ customModel: customModelValue.trim() });
                      }
                    }}
                    className="w-full h-8 px-2 border rounded text-sm font-mono"
                  />
                  <div className="text-xs text-muted-foreground space-y-1">
                    <p>Format: <code>provider/model-name</code></p>
                    <p>Examples:</p>
                    <ul className="list-disc list-inside ml-2 space-y-0.5">
                      <li><code>openai/gpt-4-1106-preview</code></li>
                      <li><code>anthropic/claude-2.1</code></li>
                      <li><code>ollama/llama2:70b</code></li>
                      <li><code>custom/your-fine-tuned-model</code></li>
                    </ul>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full h-7 text-xs"
                    onClick={() => {
                      setShowCustomInput(false);
                      setCustomModelValue("");
                      updateConfig({ customModel: null, defaultModel: "openai/gpt-4o" });
                    }}
                  >
                    Back to Preset Models
                  </Button>
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