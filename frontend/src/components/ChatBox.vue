<template>
  <div class="chat-container">
    <div class="chat-sidebar" v-if="role === 'admin'">
      <div class="sidebar-header">
        <h3>Doctors</h3>
      </div>
      <div class="sidebar-list">
        <div 
          v-for="conv in conversations" 
          :key="conv.id" 
          class="conv-pill"
          :class="{ active: selectedConv?.id === conv.id }"
          @click="selectConversation(conv)"
        >
          <div class="avatar">
            {{ conv.name.charAt(0) }}
            <div v-if="conv.unread_count > 0" class="unread-dot"></div>
          </div>
          <div class="conv-info">
            <span class="conv-name">{{ conv.name }}</span>
            <span class="conv-status">Doctor</span>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-main">
      <div v-if="selectedConv" class="chat-viewport">
        <header class="view-header">
          <div class="header-user">
            <div class="avatar">{{ selectedConv.name.charAt(0) }}</div>
            <div>
              <h4>{{ selectedConv.name }}</h4>
              <span class="role-badge">{{ selectedConv.role }}</span>
            </div>
          </div>
        </header>

        <main class="message-list" ref="messageList">
          <div v-if="loadingMessages" class="chat-loading">
            <div class="spinner"></div>
          </div>
          <div v-else-if="messages.length === 0" class="chat-empty">
            <i class="bi bi-chat-dots"></i>
            <p>No messages yet. Say hi!</p>
          </div>
          <div 
            v-for="msg in messages" 
            :key="msg.id" 
            class="msg-bubble-wrapper"
            :class="{ 'mine': isMine(msg) }"
          >
            <div class="msg-bubble">
              <p>{{ msg.content }}</p>
              <span class="msg-time">{{ formatTime(msg.timestamp) }}</span>
            </div>
          </div>
        </main>

        <footer class="input-bar">
          <input 
            v-model="newMessage" 
            placeholder="Type your message..." 
            @keyup.enter="send"
          />
          <button @click="send" :disabled="!newMessage.trim() || sending">
            <i v-if="!sending" class="bi bi-send-fill"></i>
            <div v-else class="btn-spinner"></div>
          </button>
        </footer>
      </div>
      <div v-else class="no-selection">
        <div class="no-sel-content">
          <div v-if="loadingConversations" class="conv-init-loading">
            <div class="spinner"></div>
            <p>Connecting to system...</p>
          </div>
          <template v-else>
            <div class="hero-icon"><i class="bi bi-chat-right-quote"></i></div>
            <h3>Hospital Internal Messenger</h3>
            <p v-if="role === 'admin'">Select a doctor from the list to start communicating.</p>
            <p v-else>Connect with the Hospital Administrator.</p>
            
            <!-- Removed the manual button for doctors as per user request for auto-load -->
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/interceptor'

export default {
  name: 'ChatBox',
  props: {
    role: { type: String, required: true }, // 'admin' or 'doctor'
    userId: { type: [Number, String], required: true }
  },
  data() {
    return {
      conversations: [],
      selectedConv: null,
      messages: [],
      newMessage: '',
      loadingMessages: false,
      loadingConversations: false,
      sending: false,
      pollInterval: null,
      convPollInterval: null
    }
  },
  methods: {
    async loadConversations(silent = false) {
      if (!silent) this.loadingConversations = true
      try {
        const res = await api.get('/api/chat/conversations')
        this.conversations = res.data.conversations || []
        
        // Aggressive auto-connect for doctors
        if (this.role === 'doctor' && !this.selectedConv && this.conversations.length > 0) {
            this.selectConversation(this.conversations[0])
        }
      } catch (err) {
        console.error("Chat: failed to load convas", err)
      } finally {
        if (!silent) this.loadingConversations = false
      }
    },
    async selectConversation(conv) {
      const isNew = !this.selectedConv || this.selectedConv.id !== conv.id
      this.selectedConv = conv
      if (isNew) {
        this.messages = []
        this.loadMessages()
      } else {
        this.loadMessages(true)
      }
      
      // Update unread count locally for immediate feedback
      conv.unread_count = 0
      
      // Start polling for this specific conversation
      if (this.pollInterval) clearInterval(this.pollInterval)
      this.pollInterval = setInterval(() => {
        this.loadMessages(true)
      }, 3000)
    },
    async loadMessages(silent = false) {
      if (!this.selectedConv) return
      if (!silent) this.loadingMessages = true
      try {
        const res = await api.get(`/api/chat/history/${this.selectedConv.role}/${this.selectedConv.id}`)
        const newMessages = res.data.messages || []
        
        // Always update the messages to catch any changes and ensure reactivity
        this.messages = newMessages
        if (!silent) this.scrollToBottom()
      } catch (err) {
        console.error("Chat: failed load history", err)
      } finally {
        if (!silent) this.loadingMessages = false
      }
    },
    isAtBottom() {
      const list = this.$refs.messageList
      if (!list) return true
      return list.scrollHeight - list.scrollTop <= list.clientHeight + 100
    },
    async send() {
      if (!this.newMessage.trim() || this.sending || !this.selectedConv) return
      this.sending = true
      try {
        const payload = {
          receiver_role: this.selectedConv.role,
          receiver_id: this.selectedConv.id,
          content: this.newMessage
        }
        await api.post('/api/chat/send', payload)
        this.newMessage = ''
        await this.loadMessages(true)
        this.loadConversations(true)
        this.scrollToBottom()
      } catch (err) {
        console.error("Chat: send failed", err)
        alert("Failed to send message: " + (err.response?.data?.message || err.message))
      } finally {
        this.sending = false
      }
    },
    isMine(msg) {
      if (!msg) return false
      const msgSenderId = String(msg.sender_id)
      const currentUserIdStr = String(this.userId)
      const msgSenderRole = (msg.sender_role || '').toLowerCase()
      const myRole = (this.role || '').toLowerCase()
      
      return msgSenderRole === myRole && msgSenderId === currentUserIdStr
    },
    formatTime(ts) {
      if (!ts) return ''
      const d = new Date(ts)
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const list = this.$refs.messageList
        if (list) {
          list.scrollTo({ top: list.scrollHeight, behavior: 'smooth' })
        }
      })
    }
  },
  mounted() {
    this.loadConversations()
    this.convPollInterval = setInterval(() => {
      this.loadConversations(true)
    }, 10000)
  },
  beforeUnmount() {
    if (this.pollInterval) clearInterval(this.pollInterval)
    if (this.convPollInterval) clearInterval(this.convPollInterval)
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100%;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

.chat-sidebar {
  width: 280px;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  background: #fcfcfc;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.sidebar-header h3 {
  font-size: 18px;
  margin: 0;
  color: #111827;
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.conv-pill {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.conv-pill:hover {
  background: #f3f4f6;
}

.conv-pill.active {
  background: #eef4ff;
}

.avatar {
  width: 40px;
  height: 40px;
  background: #2563eb;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
  position: relative;
}

.unread-dot {
  position: absolute;
  top: 0;
  right: 0;
  width: 10px;
  height: 10px;
  background: #10b981;
  border: 2px solid white;
  border-radius: 50%;
}

.conv-info {
  display: flex;
  flex-direction: column;
}

.conv-name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.conv-status {
  font-size: 12px;
  color: #6b7280;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
}

.chat-viewport {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.view-header {
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-user h4 {
  margin: 0;
  font-size: 16px;
}

.role-badge {
  font-size: 11px;
  text-transform: uppercase;
  color: #2563eb;
  font-weight: 700;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f9fafb;
}

.msg-bubble-wrapper {
  display: flex;
  flex-direction: column;
  max-width: 70%;
}

.msg-bubble-wrapper.mine {
  align-self: flex-end;
}

.msg-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  background: white;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.mine .msg-bubble {
  background: #2563eb;
  color: white;
  border: none;
}

.msg-bubble p {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
}

.msg-time {
  font-size: 10px;
  color: #9ca3af;
  margin-top: 4px;
  display: block;
}

.mine .msg-time {
  color: rgba(255,255,255,0.7);
  text-align: right;
}

.input-bar {
  padding: 20px 24px;
  display: flex;
  gap: 12px;
  border-top: 1px solid #f0f0f0;
}

.input-bar input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  outline: none;
}

.input-bar button {
  width: 48px;
  height: 48px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  display: grid;
  place-items: center;
}

.no-selection {
  flex: 1;
  display: grid;
  place-items: center;
  background: #f9fafb;
  text-align: center;
}

.hero-icon {
  font-size: 48px;
  color: #d1d5db;
  margin-bottom: 20px;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  margin-top: 15px;
  cursor: pointer;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #eef4ff;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.conv-init-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.conv-init-loading p {
  color: #6b7280;
  font-size: 14px;
}
</style>
