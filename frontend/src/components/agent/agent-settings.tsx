/* Copyright 2024 Marimo. All rights reserved. */
import React from "react";
import { useAgentStore } from "./stores/agent-state";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Settings, RefreshCw } from "lucide-react";

export const AgentSettings: React.FC = () => {
  const { config, availableModels, updateConfig } = useAgentStore();

  const handleModelChange = (model: string) => {
    updateConfig({
      customModel: model === config.defaultModel ? null : model,
    });
  };

  const handleSafetyModeChange = (mode: "strict" | "balanced" | "permissive") => {
    updateConfig({ safetyMode: mode });
  };

  const activeModel = config.customModel || config.defaultModel;

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
          <Settings className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Agent Configuration</DialogTitle>
          <DialogDescription>
            Configure your AI agent settings and behavior.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Model Selection */}
          <div className="space-y-2">
            <Label htmlFor="model">Model</Label>
            <Select value={activeModel} onValueChange={handleModelChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select a model" />
              </SelectTrigger>
              <SelectContent>
                {availableModels.map((model) => (
                  <SelectItem key={model} value={model}>
                    {model}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Choose your preferred AI model. Make sure you have the appropriate API keys configured.
            </p>
          </div>

          <Separator />

          {/* Behavior Settings */}
          <div className="space-y-4">
            <h4 className="font-medium">Behavior</h4>
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto-execute code</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically run generated code without approval
                </p>
              </div>
              <Switch
                checked={config.autoExecute}
                onCheckedChange={(checked) => updateConfig({ autoExecute: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Require approval</Label>
                <p className="text-sm text-muted-foreground">
                  Ask for confirmation before executing suggestions
                </p>
              </div>
              <Switch
                checked={config.requireApproval}
                onCheckedChange={(checked) => updateConfig({ requireApproval: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Stream responses</Label>
                <p className="text-sm text-muted-foreground">
                  Show responses as they are generated
                </p>
              </div>
              <Switch
                checked={config.streamResponses}
                onCheckedChange={(checked) => updateConfig({ streamResponses: checked })}
              />
            </div>

            <div className="space-y-2">
              <Label>Safety Mode</Label>
              <Select value={config.safetyMode} onValueChange={handleSafetyModeChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="strict">Strict - Maximum safety checks</SelectItem>
                  <SelectItem value="balanced">Balanced - Reasonable safety</SelectItem>
                  <SelectItem value="permissive">Permissive - Minimal restrictions</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Separator />

          {/* Advanced Settings */}
          <div className="space-y-4">
            <h4 className="font-medium">Advanced</h4>
            
            <div className="space-y-2">
              <Label>Max Steps: {config.maxSteps}</Label>
              <Slider
                value={[config.maxSteps]}
                onValueChange={([value]) => updateConfig({ maxSteps: value })}
                min={1}
                max={20}
                step={1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Maximum number of steps in an execution plan
              </p>
            </div>

            <div className="space-y-2">
              <Label>Max Tokens: {config.maxTokens}</Label>
              <Slider
                value={[config.maxTokens]}
                onValueChange={([value]) => updateConfig({ maxTokens: value })}
                min={512}
                max={8192}
                step={512}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Maximum tokens for each AI response
              </p>
            </div>

            <div className="space-y-2">
              <Label>Temperature: {config.temperature.toFixed(2)}</Label>
              <Slider
                value={[config.temperature]}
                onValueChange={([value]) => updateConfig({ temperature: value })}
                min={0}
                max={1}
                step={0.1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Controls randomness in responses (0 = deterministic, 1 = creative)
              </p>
            </div>
          </div>

          <Separator />

          {/* Environment Info */}
          <div className="space-y-2">
            <h4 className="font-medium">Environment</h4>
            <div className="text-sm text-muted-foreground space-y-1">
              <p>Configure API keys via environment variables:</p>
              <code className="text-xs bg-muted p-1 rounded">OPENAI_API_KEY</code>
              <code className="text-xs bg-muted p-1 rounded ml-1">ANTHROPIC_API_KEY</code>
              <code className="text-xs bg-muted p-1 rounded ml-1">GOOGLE_AI_API_KEY</code>
              <p className="mt-2">
                See <code className="text-xs bg-muted p-1 rounded">.env.example</code> for full configuration options.
              </p>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};