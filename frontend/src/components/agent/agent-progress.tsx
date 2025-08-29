/* Copyright 2024 Marimo. All rights reserved. */
import React from "react";
import { useAgentStore } from "./stores/agent-state";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/utils/cn";
import {
  CheckCircle,
  XCircle,
  Loader2,
  Circle,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
// import {
//   Collapsible,
//   CollapsibleContent,
//   CollapsibleTrigger,
// } from "@/components/ui/collapsible";

export const AgentProgress: React.FC = () => {
  const { currentPlan, executingStepId } = useAgentStore();
  const [isOpen, setIsOpen] = React.useState(true);

  if (currentPlan.length === 0) {
    return null;
  }

  const completedSteps = currentPlan.filter(
    (step) => step.status === "complete"
  ).length;
  const totalSteps = currentPlan.length;
  const progress = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  const getStepIcon = (status: string, isExecuting: boolean) => {
    if (isExecuting) {
      return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
    }
    switch (status) {
      case "complete":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "error":
        return <XCircle className="h-4 w-4 text-red-600" />;
      case "executing":
        return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
      default:
        return <Circle className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="border-t bg-muted/20">
      {/* Collapsible implementation simplified */}
      <div>
        <Button
          variant="ghost"
          className="w-full justify-between p-2 h-auto"
          onClick={() => setIsOpen(!isOpen)}
        >
          <div className="flex items-center gap-2">
            {isOpen ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
            <span className="text-xs font-medium">
              Execution Plan ({completedSteps}/{totalSteps})
            </span>
          </div>
          <Progress value={progress} className="w-20 h-2" />
        </Button>
        
        {isOpen && (
          <div className="px-2 pb-2 space-y-1">
            {currentPlan.map((step, index) => {
              const isExecuting = step.stepId === executingStepId;
              
              return (
                <div
                  key={step.stepId}
                  className={cn(
                    "flex items-start gap-2 p-2 rounded text-xs",
                    isExecuting && "bg-primary/10",
                    step.status === "error" && "bg-red-50 dark:bg-red-950/20"
                  )}
                >
                  <div className="mt-0.5">
                    {getStepIcon(step.status, isExecuting)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">
                        {index + 1}.
                      </span>
                      <span
                        className={cn(
                          "truncate",
                          step.status === "complete" && "line-through opacity-60"
                        )}
                      >
                        {step.description}
                      </span>
                    </div>
                    
                    {step.error && (
                      <div className="mt-1 p-1 rounded bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300">
                        {step.error}
                      </div>
                    )}
                    
                    {step.progress !== undefined && step.status === "executing" && (
                      <Progress
                        value={step.progress * 100}
                        className="mt-1 h-1"
                      />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};