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
  const showAgent = props.userConfig.ai?.agent?.enabled !== false;

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
