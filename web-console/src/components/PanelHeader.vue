<template>
  <div class="panel-toolbar">
    <div>
      <h2>{{ title }}</h2>
      <span v-if="meta" class="meta">{{ meta }}</span>
    </div>
    <div v-if="$slots.default" class="panel-toolbar-actions"><slot /></div>
  </div>
</template>

<script>
export default {
  name: 'PanelHeader',
  props: { title: { type: String, required: true }, meta: { type: String, default: '' } },
};
</script>
