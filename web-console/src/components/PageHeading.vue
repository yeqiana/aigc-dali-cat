<template>
  <div class="page-heading">
    <h1>{{ title }}</h1>
    <div v-if="$slots.default" class="page-heading-actions"><slot /></div>
  </div>
</template>

<script>
export default {
  name: 'PageHeading',
  props: { title: { type: String, required: true } },
};
</script>
