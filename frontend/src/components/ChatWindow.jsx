import { useEffect, useMemo, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import { CheckCheck, Flag, Search, Send } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getApiErrorMessage, SOCKET_URL } from '../services/api';
import { messageService } from '../services/messageService';

export default function ChatWindow({ initialConversationId = '' }) {
  const { user, token } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [selectedId, setSelectedId] = useState(initialConversationId);
  const [messages, setMessages] = useState([]);
  const [search, setSearch] = useState('');
  const [draft, setDraft] = useState('');
  const [typingUser, setTypingUser] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const socketRef = useRef(null);
  const bottomRef = useRef(null);

  const loadConversations = async () => {
    try {
      const data = await messageService.listConversations();
      const list = data.conversations || [];
      setConversations(list);
      if (!selectedId && list.length > 0) {
        setSelectedId(initialConversationId || list[0].id);
      }
    } catch (err) {
      setError(getApiErrorMessage(err, 'Could not load conversations.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!token) return undefined;
    const socket = io(SOCKET_URL, {
      auth: { token },
      transports: ['websocket', 'polling'],
    });
    socketRef.current = socket;

    socket.on('new_message', (msg) => {
      setMessages((prev) => {
        if (prev.some((m) => m.id === msg.id)) return prev;
        if (msg.conversation_id !== selectedId) return prev;
        return [...prev, msg];
      });
      setConversations((prev) =>
        prev.map((c) =>
          c.id === msg.conversation_id
            ? {
                ...c,
                last_message: msg.message,
                last_message_at: msg.sent_at,
                unread_count:
                  msg.conversation_id === selectedId || msg.sender_id === user?.id
                    ? 0
                    : (c.unread_count || 0) + 1,
              }
            : c
        )
      );
    });

    socket.on('presence_update', ({ user_id, online }) => {
      setConversations((prev) =>
        prev.map((c) =>
          c.other_user?.id === user_id
            ? { ...c, other_user: { ...c.other_user, online } }
            : c
        )
      );
    });

    socket.on('typing', ({ conversation_id, is_typing }) => {
      if (conversation_id === selectedId) {
        setTypingUser(Boolean(is_typing));
      }
    });

    socket.on('messages_read', ({ conversation_id }) => {
      if (conversation_id === selectedId) {
        setMessages((prev) =>
          prev.map((m) => (m.read_at ? m : { ...m, read_at: new Date().toISOString() }))
        );
      }
    });

    return () => {
      socket.disconnect();
    };
  }, [token, selectedId, user?.id]);

  useEffect(() => {
    if (!selectedId) return;
    let active = true;
    messageService
      .getMessages(selectedId)
      .then((data) => {
        if (!active) return;
        setMessages(data.messages || []);
        setConversations((prev) =>
          prev.map((c) => (c.id === selectedId ? { ...c, unread_count: 0 } : c))
        );
        socketRef.current?.emit('join_conversation', { conversation_id: selectedId });
        socketRef.current?.emit('mark_read', { conversation_id: selectedId });
      })
      .catch((err) => {
        if (active) setError(getApiErrorMessage(err, 'Failed to load chat history.'));
      });

    return () => {
      active = false;
      socketRef.current?.emit('leave_conversation', { conversation_id: selectedId });
    };
  }, [selectedId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const filteredConversations = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return conversations;
    return conversations.filter((c) =>
      `${c.other_user?.full_name || ''} ${c.other_user?.specialization || ''} ${c.last_message || ''}`
        .toLowerCase()
        .includes(q)
    );
  }, [conversations, search]);

  const selectedConv = conversations.find((c) => c.id === selectedId);

  const handleSend = async (e) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || !selectedId) return;
    setDraft('');
    setError('');
    try {
      const data = await messageService.sendMessage({
        conversation_id: selectedId,
        message: text,
      });
      const saved = data.message;
      setMessages((prev) => (prev.some((m) => m.id === saved.id) ? prev : [...prev, saved]));
      setConversations((prev) =>
        prev.map((c) =>
          c.id === selectedId ? { ...c, last_message: saved.message, last_message_at: saved.sent_at } : c
        )
      );
      socketRef.current?.emit('typing', { conversation_id: selectedId, is_typing: false });
    } catch (err) {
      setError(getApiErrorMessage(err, 'Message could not be sent.'));
    }
  };

  const handleReport = async () => {
    if (!selectedId) return;
    const reason = window.prompt('Describe why you are reporting this conversation for moderation:');
    if (!reason || !reason.trim()) return;
    try {
      await messageService.reportConversation(selectedId, reason.trim());
      setNotice('Conversation has been flagged for administrator moderation review.');
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  if (loading) {
    return (
      <div className="card" style={{ display: 'grid', placeItems: 'center', minHeight: 320 }}>
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div>
      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="messenger-layout">
        <div className="messenger-sidebar">
          <div className="messenger-search">
            <div style={{ position: 'relative' }}>
              <Search size={16} style={{ position: 'absolute', left: 10, top: 11, color: '#64748b' }} />
              <input
                type="text"
                className="form-input"
                placeholder="Search conversations..."
                style={{ paddingLeft: '2rem' }}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>

          <div className="conversation-list">
            {filteredConversations.length === 0 ? (
              <div style={{ padding: '1.25rem', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                No conversations yet. Start a conversation from Consultations or Find Doctor.
              </div>
            ) : (
              filteredConversations.map((conv) => (
                <button
                  key={conv.id}
                  type="button"
                  className={`conversation-item ${conv.id === selectedId ? 'active' : ''}`}
                  onClick={() => setSelectedId(conv.id)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.45rem' }}>
                      <span className={`presence-dot ${conv.other_user?.online ? 'presence-online' : 'presence-offline'}`} />
                      {conv.other_user?.full_name}
                    </span>
                    {conv.unread_count > 0 && (
                      <span className="badge badge-diabetic">{conv.unread_count}</span>
                    )}
                  </div>
                  {conv.other_user?.specialization && (
                    <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                      {conv.other_user.specialization}
                    </span>
                  )}
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {conv.last_message || 'No messages yet'}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>

        <div className="messenger-chat">
          {selectedConv ? (
            <>
              <div className="chat-header">
                <div>
                  <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className={`presence-dot ${selectedConv.other_user?.online ? 'presence-online' : 'presence-offline'}`} />
                    {selectedConv.other_user?.full_name}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {selectedConv.other_user?.online ? 'Online' : 'Offline'}
                    {typingUser ? ' • typing...' : ''}
                  </div>
                </div>
                <button type="button" className="btn btn-secondary btn-sm" onClick={handleReport}>
                  <Flag size={14} />
                  Report
                </button>
              </div>

              <div className="chat-messages">
                {messages.map((msg) => {
                  const mine = msg.sender_id === user?.id;
                  return (
                    <div key={msg.id} className={`chat-bubble ${mine ? 'chat-bubble-mine' : 'chat-bubble-theirs'}`}>
                      <div>{msg.message}</div>
                      <div className="chat-meta">
                        <span>{msg.sent_at ? new Date(msg.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</span>
                        {mine && <CheckCheck size={13} color={msg.read_at ? '#a7f3d0' : '#cbd5e1'} />}
                      </div>
                    </div>
                  );
                })}
                <div ref={bottomRef} />
              </div>

              <form className="chat-input-bar" onSubmit={handleSend}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Write a message..."
                  value={draft}
                  onChange={(e) => {
                    setDraft(e.target.value);
                    socketRef.current?.emit('typing', {
                      conversation_id: selectedId,
                      is_typing: Boolean(e.target.value.trim()),
                    });
                  }}
                />
                <button type="submit" className="btn btn-primary" disabled={!draft.trim()}>
                  <Send size={16} />
                  Send
                </button>
              </form>
            </>
          ) : (
            <div style={{ display: 'grid', placeItems: 'center', height: '100%', color: 'var(--text-muted)' }}>
              Select a conversation to begin messaging.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
