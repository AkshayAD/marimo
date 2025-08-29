/* Copyright 2024 Marimo. All rights reserved. */

import type { AppConfig, UserConfig } from "@/core/config/config-schema";
import { KnownQueryParams } from "@/core/constants";
import { EditApp } from "@/core/edit-app";
import { AppChrome } from "../editor/chrome/wrapper/app-chrome";
import { CommandPalette } from "../editor/controls/command-palette";
import { AgentPanel } from "../agent/agent-panel";

interface Props {
  userConfig: UserConfig;
  appConfig: AppConfig;
}

const hideChrome = (() => {
  const url = new URL(window.location.href);
  return url.searchParams.get(KnownQueryParams.showChrome) === "false";
})();

const EditPage = (props: Props) => {
  // Agent feature is enabled by default unless explicitly disabled
  const aiConfig = props.userConfig.ai as any;
  const showAgent = aiConfig?.agent?.enabled !== false;

  if (hideChrome) {
    return (
      <>
        <EditApp hideControls={true} {...props} />
        <CommandPalette />
        {showAgent && <AgentPanel />}
      </>
    );
  }

  return (
    <AppChrome>
      <EditApp {...props} />
      <CommandPalette />
      {showAgent && <AgentPanel />}
    </AppChrome>
  );
};

export default EditPage;
