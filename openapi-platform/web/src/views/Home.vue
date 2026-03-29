<template>
  <div class="card">
    <h2>欢迎使用 OpenAPI 平台</h2>
    <p class="text-light">统一接口托管与对外服务平台</p>
    <div class="mt-4">
      <h3>功能概览</h3>
      <ul style="margin-top: 12px; padding-left: 20px;">
        <li>接口发布与托管 - 轻松管理您的 API</li>
        <li>API 密钥认证 - 简单安全的访问控制</li>
        <li>OAuth2.0 授权 - 标准化的第三方授权</li>
        <li>JWT 令牌认证 - 轻量级的身份验证</li>
      </ul>
    </div>
    <div class="mt-4 flex">
      <router-link to="/apis" class="btn btn-primary">管理接口</router-link>
      <router-link to="/api-keys" class="btn btn-primary">管理密钥</router-link>
      <router-link to="/oauth-apps" class="btn btn-primary">管理OAuth</router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home'
}
</script>
