<template>
  <header class="app-header">
    <div class="breadcrumb-wrap">
      <span class="header-context">STORYOS</span>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item>控制台</el-breadcrumb-item>
        <el-breadcrumb-item>{{ $route.meta.title || '页面' }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
  </header>
</template>

<script>
export default {};
</script>
