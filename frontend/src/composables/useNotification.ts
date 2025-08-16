import { ElMessage, ElNotification } from 'element-plus'

export function useNotification() {
  const showSuccess = (message: string, title?: string) => {
    if (title) {
      ElNotification({
        title,
        message,
        type: 'success',
        duration: 3000
      })
    } else {
      ElMessage({
        message,
        type: 'success',
        duration: 3000
      })
    }
  }

  const showError = (message: string, title?: string) => {
    if (title) {
      ElNotification({
        title,
        message,
        type: 'error',
        duration: 5000
      })
    } else {
      ElMessage({
        message,
        type: 'error',
        duration: 5000
      })
    }
  }

  const showWarning = (message: string, title?: string) => {
    if (title) {
      ElNotification({
        title,
        message,
        type: 'warning',
        duration: 4000
      })
    } else {
      ElMessage({
        message,
        type: 'warning',
        duration: 4000
      })
    }
  }

  const showInfo = (message: string, title?: string) => {
    if (title) {
      ElNotification({
        title,
        message,
        type: 'info',
        duration: 3000
      })
    } else {
      ElMessage({
        message,
        type: 'info',
        duration: 3000
      })
    }
  }

  return {
    showSuccess,
    showError,
    showWarning,
    showInfo
  }
}