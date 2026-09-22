<template>
  <main class="login-page">
    <section class="login-panel">
      <div class="login-card">
        <div class="login-heading">
          <div class="brand-mark">S<span>O</span></div>
          <h1>登录 StoryOS</h1>
        </div>
        <el-form ref="form" :model="form" :rules="rules" label-position="top" @submit.native.prevent="submit">
          <el-form-item label="账户" prop="username">
            <el-input v-model="form.username" prefix-icon="el-icon-user" autocomplete="username" placeholder="输入账户" @keyup.enter.native="submit" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" prefix-icon="el-icon-lock" type="password" show-password autocomplete="current-password" placeholder="输入密码" @keyup.enter.native="submit" />
          </el-form-item>
          <el-button class="login-submit" type="primary" :loading="loading" native-type="submit">进入控制台</el-button>
        </el-form>
        <p v-if="errorMessage" class="login-error">{{ errorMessage }}</p>
      </div>
    </section>
  </main>
</template>

<script>
export default {
  data() {
    return {
      loading: false,
      errorMessage: '',
      form: { username: 'admin', password: '' },
      rules: {
        username: [{ required: true, message: '请输入账户', trigger: 'blur' }],
        password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
      },
    };
  },
  methods: {
    submit() {
      this.$refs.form.validate((valid) => {
        if (!valid) return;
        this.loading = true;
        this.errorMessage = '';
        this.$store.dispatch('auth/login', this.form)
          .then(() => {
            const redirect = this.$route.query.redirect || '/production';
            this.$message.success('登录成功');
            this.$router.replace(redirect);
          })
          .catch((error) => { this.errorMessage = error.message; })
          .finally(() => { this.loading = false; });
      });
    },
  },
};
</script>
