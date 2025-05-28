<template>
  <div class="chat-page-container d-flex flex-column vh-100">
    <div class="d-flex flex-grow-1 overflow-hidden">
      <div class="conversations-sidebar border-end bg-light d-none d-lg-flex flex-column" style="width: 320px;">
        <div class="p-3 border-bottom">
          <button class="btn btn-primary w-100 d-flex align-items-center justify-content-center" @click="startNewConversation">
            <i class="bi bi-plus-circle me-2"></i>New Chat
          </button>
        </div>
        <div class="list-group list-group-flush flex-grow-1 overflow-auto">
          <a
            href="#"
            v-for="conv in conversations"
            :key="conv.id"
            class="list-group-item list-group-item-action py-3"
            :class="{ active: currentConversationId === conv.id }"
            @click.prevent="selectConversation(conv.id)"
          >
            <div class="d-flex w-100 justify-content-between">
              <h6 class="mb-1 text-truncate fw-normal">{{ conv.title || `Conversation ${conv.id}` }}</h6>
              <small class="text-muted flex-shrink-0 ms-2">{{ formatTimestamp(conv.updated_at) }}</small>
            </div>
          </a>
          <div v-if="isLoadingConversations" class="text-center p-3 text-muted">
            <div class="spinner-border spinner-border-sm" role="status"></div> Loading...
          </div>
          <div v-if="!isLoadingConversations && !conversations.length" class="text-center p-3 text-muted">
            No conversations yet.
          </div>
        </div>
      </div>

      <div class="chat-window d-flex flex-column flex-grow-1 bg-white">
         <div class="p-2 border-bottom d-lg-none">
            <button class="btn btn-outline-secondary btn-sm" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasConversations" aria-controls="offcanvasConversations">
                <i class="bi bi-list"></i> Conversations
            </button>
        </div>

        <!-- Placeholder: Shown initially -->
        <div v-if="chatUiState === 'INITIAL_PLACEHOLDER'" class="d-flex flex-column justify-content-center align-items-center h-100 p-3 text-center">
          <i class="bi bi-chat-quote-fill display-1 text-light-emphasis"></i>
          <p class="mt-3 fs-5 text-muted">Select a conversation or start a new one.</p>
          <button class="btn btn-primary mt-2 d-lg-none" @click="startNewConversation">
            <i class="bi bi-plus-circle me-2"></i>New Chat
          </button>
        </div>
        
        <template v-else-if="chatUiState === 'CHATTING_UI_ACTIVE'">
          <div class="chat-header p-3 border-bottom d-flex justify-content-between align-items-center bg-light-subtle">
              <h5 class="mb-0 text-truncate fw-normal">{{ currentConversationId ? currentConversationTitle : 'New Chat' }}</h5>
          </div>
          <div class="chat-messages flex-grow-1 p-3 overflow-auto" ref="chatMessagesContainerRef">
            <div v-if="isLoadingMessages" class="text-center py-5">
              <div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>
            </div>
            <div v-for="(message, index) in currentMessages" :key="`msg-${currentConversationId}-${index}-${message.created_at}`" 
                 :class="['d-flex mb-3', message.role === 'user' ? 'justify-content-end' : 'justify-content-start']">
              <div :class="['p-2 px-3 rounded-3 shadow-sm message-content', message.role === 'user' ? 'bg-primary text-white' : 'bg-light-subtle text-dark border']"
                   style="max-width: 75%; word-wrap: break-word;">
                <!-- MODIFIED: Use v-html for AI messages to render Markdown, v-text for user messages -->
                <div v-if="message.role === 'user'" v-text="message.content"></div>
                <div v-else v-html="renderMarkdown(message.content)"></div> 
                <small :class="['d-block mt-1', message.role === 'user' ? 'text-white-50 text-end' : 'text-muted text-start']" style="font-size: 0.75rem;">
                  {{ message.role === 'user' ? 'You' : 'AI' }} - {{ formatMessageTimestamp(message.created_at) }}
                </small>
              </div>
            </div>
            <div v-if="isAiTyping" class="d-flex justify-content-start mb-3">
                <div class="p-2 px-3 rounded-3 shadow-sm bg-light-subtle text-dark border" style="max-width: 75%;">
                    <div class="d-flex align-items-center">
                        <span class="spinner-grow spinner-grow-sm me-2 text-primary" role="status" aria-hidden="true"></span>
                        <span class="text-muted">AI is thinking...</span>
                    </div>
                </div>
            </div>
          </div>

          <div class="chat-input-area p-3 border-top bg-light-subtle">
            <form @submit.prevent="sendMessage">
              <div class="input-group">
                <input
                  type="text"
                  v-model="newMessage"
                  class="form-control form-control-lg"
                  placeholder="Type your message..."
                  :disabled="isAiTyping || isLoadingMessages"
                  required
                  ref="messageInputRef"
                />
                <button class="btn btn-primary btn-lg" type="submit" :disabled="isAiTyping || isLoadingMessages || !newMessage.trim()">
                  <span v-if="isAiTyping" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  <i v-else class="bi bi-send-fill"></i>
                </button>
              </div>
            </form>
          </div>
        </template>
      </div>
    </div>

    <!-- Offcanvas Sidebar for Mobile -->
    <div class="offcanvas offcanvas-start" tabindex="-1" id="offcanvasConversations" aria-labelledby="offcanvasConversationsLabel" style="width: 300px;">
        <div class="offcanvas-header border-bottom">
            <h5 class="offcanvas-title" id="offcanvasConversationsLabel">Conversations</h5>
            <button type="button" class="btn-close" data-bs-dismiss="offcanvas" aria-label="Close"></button>
        </div>
        <div class="offcanvas-body p-0">
             <div class="p-3 border-bottom">
                <button 
                    class="btn btn-primary w-100 d-flex align-items-center justify-content-center" 
                    @click="startNewConversationAndCloseOffcanvas">
                    <i class="bi bi-plus-circle me-2"></i>New Chat
                </button>
            </div>
            <div class="list-group list-group-flush flex-grow-1 overflow-auto">
                <a href="#" v-for="conv in conversations" :key="conv.id"
                   class="list-group-item list-group-item-action py-3"
                   :class="{ active: currentConversationId === conv.id }"
                   @click.prevent="selectConversationAndCloseOffcanvas(conv.id)">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1 text-truncate fw-normal">{{ conv.title || `Conversation ${conv.id}` }}</h6>
                        <small class="text-muted flex-shrink-0 ms-2">{{ formatTimestamp(conv.updated_at) }}</small>
                    </div>
                </a>
                 <div v-if="isLoadingConversations" class="text-center p-3 text-muted">
                    <div class="spinner-border spinner-border-sm" role="status"></div> Loading...
                 </div>
                 <div v-if="!isLoadingConversations && !conversations.length" class="text-center p-3 text-muted">
                    No conversations yet.
                 </div>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed, watch } from 'vue';
import axios from 'axios';
import { Offcanvas } from 'bootstrap'; 
import { marked } from 'marked'; 

const chatMessagesContainerRef = ref(null);
const messageInputRef = ref(null);
let offcanvasInstance = null; 

const conversations = ref([]);
const currentConversationId = ref(null);
const currentMessages = ref([]);
const newMessage = ref('');
const isLoadingConversations = ref(false);
const isLoadingMessages = ref(false);
const isAiTyping = ref(false);
const chatUiState = ref('INITIAL_PLACEHOLDER');

const API_URL = 'http://127.0.0.1:8000/chat';
const token = localStorage.getItem('token');
const authHeaders = { Authorization: `Bearer ${token}` };

const currentConversationTitle = computed(() => {
    const conv = conversations.value.find(c => c.id === currentConversationId.value);
    return conv ? (conv.title || `Conversation ${conv.id}`) : 'Chat'; 
});

const renderMarkdown = (text) => {
  if (text) {

    marked.use({
      renderer: {
        link(href, title, text) {
          const link = marked.Renderer.prototype.link.call(this, href, title, text);
          return link.replace("<a", "<a target='_blank' rel='noopener noreferrer'");
        }
      },

    });
    const dirtyHtml = marked.parse(text);

    return dirtyHtml; 
  }
  return '';
};

// --- Core Chat Logic ---
const fetchConversations = async () => {
  isLoadingConversations.value = true;
  try {
    const response = await axios.get(`${API_URL}/conversations`, { headers: authHeaders });
    conversations.value = response.data.sort((a,b) => new Date(b.updated_at) - new Date(a.updated_at));
  } catch (error) { console.error('Error fetching conversations:', error); } 
  finally { isLoadingConversations.value = false; }
};

const selectConversation = async (id) => {
  if (isLoadingMessages.value || isAiTyping.value || currentConversationId.value === id) return;
  
  currentConversationId.value = id;
  isLoadingMessages.value = true;
  currentMessages.value = [];
  chatUiState.value = 'CHATTING_UI_ACTIVE'; 

  try {
    const response = await axios.get(`${API_URL}/conversations/${id}`, { headers: authHeaders });
    currentMessages.value = response.data;
    scrollToBottom();
    focusMessageInput();
  } catch (error) { 
    console.error(`Error fetching messages for conversation ${id}:`, error);
  } finally { 
    isLoadingMessages.value = false; 
  }
};

const startNewConversation = () => {
  console.log('startNewConversation core action triggered');
  currentConversationId.value = null; 
  currentMessages.value = [];
  newMessage.value = '';
  chatUiState.value = 'CHATTING_UI_ACTIVE'; 
  focusMessageInput();
};

const startNewConversationAndCloseOffcanvas = () => {
    startNewConversation();
    if (offcanvasInstance && typeof offcanvasInstance.hide === 'function') {
        try { offcanvasInstance.hide(); } catch (e) { console.error("Error hiding offcanvas:", e); }
    } else { console.warn('Offcanvas instance not available for programmatic closing.'); }
};

const selectConversationAndCloseOffcanvas = (id) => {
    selectConversation(id); 
    if (offcanvasInstance && typeof offcanvasInstance.hide === 'function') {
         try { offcanvasInstance.hide(); } catch (e) { console.error("Error hiding offcanvas:", e); }
    } else { console.warn('Offcanvas instance not available for programmatic closing.'); }
};

const sendMessage = async () => {
  if (!newMessage.value.trim()) return;

  const userMessageContent = newMessage.value.trim();
  const tempUserMessage = { 
      role: 'user', 
      content: userMessageContent, 
      created_at: new Date().toISOString() 
  };
  currentMessages.value.push(tempUserMessage);
  
  const localNewMessage = newMessage.value; 
  newMessage.value = '';
  scrollToBottom();
  isAiTyping.value = true;

  const payload = {
    query: localNewMessage.trim(),
    conversation_id: currentConversationId.value,
  };

  try {
    const response = await axios.post(`${API_URL}/`, payload, { headers: authHeaders });
    currentMessages.value = response.data.history; 
    
    if (!currentConversationId.value && response.data.conversation_id) { 
        currentConversationId.value = response.data.conversation_id;
        const newConvData = {
            id: response.data.conversation_id,
            title: response.data.history[0]?.content.substring(0,30) + (response.data.history[0]?.content.length > 30 ? '...' : '') || `Chat ${response.data.conversation_id}`,
            updated_at: response.data.history[response.data.history.length -1]?.created_at || new Date().toISOString()
        };
        conversations.value.unshift(newConvData);
        conversations.value.sort((a,b) => new Date(b.updated_at) - new Date(a.updated_at));
    } else if (currentConversationId.value) { 
        const convIndex = conversations.value.findIndex(c => c.id === currentConversationId.value);
        if (convIndex !== -1) {
            conversations.value[convIndex].updated_at = response.data.history[response.data.history.length -1]?.created_at || new Date().toISOString();
            if (conversations.value[convIndex].title.startsWith('Conversation ') || conversations.value[convIndex].title.startsWith('Chat ')) {
                 conversations.value[convIndex].title = response.data.history[0]?.content.substring(0,30) + (response.data.history[0]?.content.length > 30 ? '...' : '') || conversations.value[convIndex].title;
            }
            conversations.value.sort((a,b) => new Date(b.updated_at) - new Date(a.updated_at));
        }
    }
    scrollToBottom();
  } catch (error) {
    console.error('Error sending message:', error);
    const optimisticMsgIndex = currentMessages.value.findIndex(m => m === tempUserMessage);
    if (optimisticMsgIndex > -1) currentMessages.value.splice(optimisticMsgIndex, 1);
    
    currentMessages.value.push({ 
        role: 'system', 
        content: 'Error: Could not get response from AI.', 
        created_at: new Date().toISOString() 
    });
  } finally {
    isAiTyping.value = false;
    focusMessageInput();
  }
};

// --- UI Helper Functions ---
const scrollToBottom = () => {
  nextTick(() => {
    if (chatMessagesContainerRef.value) {
      chatMessagesContainerRef.value.scrollTop = chatMessagesContainerRef.value.scrollHeight;
    }
  });
};

const focusMessageInput = () => {
    nextTick(() => {
        if(messageInputRef.value) {
            messageInputRef.value.focus();
        }
    });
};

watch(currentMessages, () => { scrollToBottom(); }, { deep: true });

const formatTimestamp = (timestamp) => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  const today = new Date();
  if (date.toDateString() === today.toDateString()) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  return date.toLocaleDateString([], { month: 'short', day: 'numeric'});
};

const formatMessageTimestamp = (timestamp) => {
     if (!timestamp) return '';
     const date = new Date(timestamp);
     return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
};

// --- Lifecycle Hook ---
onMounted(async () => {
  await fetchConversations(); 
  // chatUiState remains 'INITIAL_PLACEHOLDER' by default

  const offcanvasElement = document.getElementById('offcanvasConversations');
  if (offcanvasElement) {
    if (typeof Offcanvas !== 'undefined') {
        try {
            offcanvasInstance = new Offcanvas(offcanvasElement);
        } catch (e) {
            console.error("Error initializing Offcanvas with imported class:", e);
            offcanvasInstance = null; 
        }
    } else {
        console.warn("Imported Bootstrap Offcanvas class not found.");
    }
  } else {
    console.error("Offcanvas element with ID 'offcanvasConversations' not found.");
  }
});

</script>

<style scoped>
.chat-page-container {
  padding-top: 56px; 
  height: 100vh; 
  box-sizing: border-box;
}
.chat-page-container > .d-flex { 
    height: calc(100% - 0px); 
}

.conversations-sidebar, .chat-window {
  height: 100%; 
}
.list-group-item small { font-size: 0.8em; }
.chat-messages { scrollbar-width: thin; scrollbar-color: #adb5bd #f8f9fa; }
.chat-messages::-webkit-scrollbar { width: 8px; }
.chat-messages::-webkit-scrollbar-track { background: #f8f9fa; }
.chat-messages::-webkit-scrollbar-thumb { background-color: #adb5bd; border-radius: 10px; border: 2px solid #f8f9fa; }

.message-content { 
  line-height: 1.5; 
}

/* Styles for Markdown content rendered by v-html */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3),
.message-content :deep(h4),
.message-content :deep(h5),
.message-content :deep(h6) {
  margin-top: 0.75em;
  margin-bottom: 0.25em;
  font-weight: 600; /* Or as per your design */
}
.message-content :deep(h1) { font-size: 1.5rem; }
.message-content :deep(h2) { font-size: 1.35rem; }
.message-content :deep(h3) { font-size: 1.2rem; }

.message-content :deep(p) {
  margin-bottom: 0.5em;
}
.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  padding-left: 1.5em; 
  margin-bottom: 0.5em;
}
.message-content :deep(li) {
  margin-bottom: 0.2em;
}

.message-content :deep(strong) {
  font-weight: bold;
}
.message-content :deep(em) {
  font-style: italic;
}

.message-content :deep(a) {
  color: var(--bs-primary); /* Or your theme's link color */
  text-decoration: underline;
}
.message-content :deep(a:hover) {
  color: var(--bs-primary-darken); /* Darken on hover */
}

.message-content :deep(pre) {
  background-color: #f8f9fa; /* Light background for code blocks */
  border: 1px solid #dee2e6; /* Border for code blocks */
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto; /* Scroll for long lines */
  font-size: 0.9em;
  margin: 0.5em 0;
}
.message-content :deep(code) {
  font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  background-color: #e9ecef; /* Lighter background for inline code */
  padding: 0.1em 0.4em;
  border-radius: 3px;
  font-size: 0.9em;
}
.message-content :deep(pre code) {
  background-color: transparent; /* No double background for code inside pre */
  padding: 0;
  border: none;
  font-size: 1em; /* Inherit from pre */
}

.message-content :deep(blockquote) {
  border-left: 3px solid #adb5bd;
  padding-left: 1em;
  margin-left: 0;
  margin-right: 0;
  color: #6c757d;
}

.message-content :deep(hr) {
    margin-top: 1rem;
    margin-bottom: 1rem;
    border: 0;
    border-top: 1px solid rgba(0, 0, 0, 0.1);
}

/* Basic table styling, Bootstrap might provide better defaults */
.message-content :deep(table) {
  width: 100%;
  margin-bottom: 1rem;
  color: #212529;
  border-collapse: collapse;
}
.message-content :deep(th),
.message-content :deep(td) {
  padding: 0.5rem;
  vertical-align: top;
  border-top: 1px solid #dee2e6;
}
.message-content :deep(thead th) {
  vertical-align: bottom;
  border-bottom: 2px solid #dee2e6;
  background-color: #f8f9fa;
}
.message-content :deep(tbody + tbody) {
  border-top: 2px solid #dee2e6;
}
</style>