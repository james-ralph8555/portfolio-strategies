import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community';

let registered = false;

export const ensureAgGridModules = () => {
  if (registered) return;

  ModuleRegistry.registerModules([AllCommunityModule]);
  registered = true;
};
