const state = { sidebarCollapsed: false };

const mutations = {
  TOGGLE_SIDEBAR(state) { state.sidebarCollapsed = !state.sidebarCollapsed; },
};

export default { namespaced: true, state, mutations };
