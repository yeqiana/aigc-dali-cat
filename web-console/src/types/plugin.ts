export interface PluginDefinition {
  pluginId: string;
  name: string;
  type: string;
  status: string;
  version?: string;
}

export interface ExtensionPoint {
  id: string;
  name: string;
  capability: string;
}
