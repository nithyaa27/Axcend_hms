<template>
  <div class="floating-chat-container" :class="{ 'is-maximized': isMaximized }">
    <!-- Chat FAB (Floating Action Button) -->
    <button 
      v-if="!isOpen" 
      class="chat-fab" 
      @click="openChat"
    >
      <i class="bi bi-chat-dots-fill"></i>
      <div v-if="unreadCount > 0" class="fab-badge">{{ unreadCount }}</div>
    </button>

    <!-- Chat Popup Window -->
    <div v-else class="chat-window" :class="{'admin-size': role === 'admin'}">
      <div class="window-header">
        <div class="header-title">
          <i class="bi bi-chat-text"></i>
          <span>Internal Chat</span>
        </div>
        <div class="header-controls">
          <button @click="minimize" title="Minimize"><i class="bi bi-dash"></i></button>
          <button @click="toggleMaximize" :title="isMaximized ? 'Restore' : 'Maximize'">
            <i :class="isMaximized ? 'bi bi-fullscreen-exit' : 'bi bi-fullscreen'"></i>
          </button>
          <button @click="close" title="Close"><i class="bi bi-x"></i></button>
        </div>
      </div>
      <div class="window-body">
        <ChatBox :role="role" :userId="userId" />
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/interceptor'
import ChatBox from '@/components/ChatBox.vue'

export default {
  name: 'FloatingChat',
  components: { ChatBox },
  props: {
    role: { type: String, required: true },
    userId: { type: [Number, String], required: true }
  },
  data() {
    return {
      isOpen: false,
      isMaximized: false,
      unreadCount: 0,
      badgelLoop: null
    }
  },
  methods: {
    openChat() {
      this.isOpen = true;
    },
    minimize() {
      this.isOpen = false;
      this.isMaximized = false;
    },
    close() {
      this.isOpen = false;
      this.isMaximized = false;
    },
    toggleMaximize() {
      this.isMaximized = !this.isMaximized;
    },
    async checkUnread() {
      try {
        const res = await api.get('/api/chat/unread-total');
        this.unreadCount = res.data.count || 0;
      } catch (err) {
        // ignore
      }
    }
  },
  mounted() {
    this.checkUnread();
    this.badgelLoop = setInterval(this.checkUnread, 5000);
  },
  beforeUnmount() {
    if (this.badgelLoop) clearInterval(this.badgelLoop);
  }
}
</script>

<style scoped>
.floating-chat-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
}

/* Maximize State Override */
.floating-chat-container.is-maximized {
  bottom: 0;
  right: 0;
  width: 100vw;
  height: 100vh;
}

/* The FAB */
.chat-fab {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: #2563eb;
  color: white;
  border: none;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
  display: grid;
  place-items: center;
  position: relative;
  transition: transform 0.2s;
}

.chat-fab:hover {
  transform: scale(1.05);
}

.fab-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background-color: #ef4444;
  color: white;
  font-size: 12px;
  font-weight: bold;
  height: 22px;
  min-width: 22px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
}

/* The Window */
.chat-window {
  background: white;
  width: 400px;
  height: 600px;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.chat-window.admin-size {
  width: 700px;
}

.is-maximized .chat-window {
  width: 100%;
  height: 100%;
  border-radius: 0;
  border: none;
}

/* Header */
.window-header {
  background: #1e3a8a;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
}

.header-controls {
  display: flex;
  gap: 8px;
}

.header-controls button {
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  display: grid;
  place-items: center;
  font-size: 20px;
}

.header-controls button:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* Body */
.window-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  background: #f9fafb;
}

/* Ensure ChatBox spans 100% inside our popup */
.window-body > * {
  width: 100%;
  height: 100%;
}
</style>
