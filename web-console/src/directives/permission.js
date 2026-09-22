import Vue from 'vue';

export function registerPermissionDirective(store) {
  Vue.directive('permission', {
    inserted(el, binding) {
      const permission = binding.value;
      if (permission && !store.getters['auth/can'](permission)) el.parentNode?.removeChild(el);
    },
  });
}
