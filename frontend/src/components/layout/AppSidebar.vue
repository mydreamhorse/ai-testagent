<template>
  <div class="sidebar-container">
    <el-menu
      :default-active="activeMenu"
      router
      class="sidebar-menu"
      background-color="#f5f7fa"
      text-color="#333"
      active-text-color="#409eff"
    >
      <el-menu-item index="/dashboard">
        <el-icon><Odometer /></el-icon>
        <span>仪表盘</span>
      </el-menu-item>
      
      <el-menu-item index="/requirements">
        <el-icon><Document /></el-icon>
        <span>需求管理</span>
      </el-menu-item>
      
      <el-menu-item index="/test-cases">
        <el-icon><List /></el-icon>
        <span>测试用例</span>
      </el-menu-item>
      
      <el-menu-item index="/generation">
        <el-icon><MagicStick /></el-icon>
        <span>智能生成</span>
      </el-menu-item>
      
      <el-menu-item index="/analytics">
        <el-icon><DataAnalysis /></el-icon>
        <span>数据分析</span>
      </el-menu-item>
      
      <el-menu-item index="/knowledge">
        <el-icon><Collection /></el-icon>
        <span>知识管理</span>
      </el-menu-item>
      
      <el-menu-item index="/templates">
        <el-icon><Files /></el-icon>
        <span>模板管理</span>
      </el-menu-item>
      
      <el-sub-menu index="system">
        <template #title>
          <el-icon><Setting /></el-icon>
          <span>系统管理</span>
        </template>
        <el-menu-item index="/system/users">用户管理</el-menu-item>
        <el-menu-item index="/system/settings">系统设置</el-menu-item>
      </el-sub-menu>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const activeMenu = computed(() => {
  return route.path
})
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  overflow-y: auto;
}

.sidebar-menu {
  height: 100%;
  border-right: none;
}

.sidebar-menu .el-menu-item {
  height: 50px;
  line-height: 50px;
  padding-left: 20px !important;
}

.sidebar-menu .el-sub-menu .el-menu-item {
  height: 45px;
  line-height: 45px;
  padding-left: 40px !important;
}

.sidebar-menu .el-menu-item:hover {
  background-color: #e6f7ff;
}

.sidebar-menu .el-menu-item.is-active {
  background-color: #e6f7ff;
  border-right: 3px solid #409eff;
}
</style>