import { pluginApi } from '../api/plugin';

export default function PluginConsole() {
  async function loadPlugins() {
    await pluginApi.list();
  }

  return (
    <section>
      <h2>Plugin / Extension Console</h2>
      <button onClick={loadPlugins}>Load Plugins</button>
      <p>Plugin Registry and Extension Points</p>
    </section>
  );
}
