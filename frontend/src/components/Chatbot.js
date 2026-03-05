import React, { useState, useRef, useEffect } from 'react';
import { Box, Paper, TextField, IconButton, Typography, Avatar, Fab } from '@mui/material';
import { Send, Close, SupportAgent } from '@mui/icons-material';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const Chatbot = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { text: "Hi! I'm your travel assistant. Ask me anything about travel planning!", sender: 'bot' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setMessages(prev => [...prev, { text: userMessage, sender: 'user' }]);
    setInput('');
    setLoading(true);

    try {
      const conversationHistory = messages.map(m => m.text);
      const response = await axios.post('http://localhost:8000/chatbot', {
        message: userMessage,
        conversation_history: conversationHistory
      });

      setMessages(prev => [...prev, { text: response.data.response, sender: 'bot' }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        text: 'Sorry, I encountered an error. Please try again.', 
        sender: 'bot' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      <Fab
        sx={{ 
          position: 'fixed', 
          bottom: 20, 
          right: 20, 
          zIndex: 1001,
          bgcolor: '#ff9800',
          '&:hover': { bgcolor: '#f57c00' }
        }}
        onClick={() => setOpen(!open)}
      >
        {open ? <Close sx={{ color: 'white' }} /> : <SupportAgent sx={{ color: 'white' }} />}
      </Fab>

      {open && (
        <Paper
          elevation={8}
          sx={{
            position: 'fixed',
            bottom: 90,
            right: 20,
            width: 350,
            height: 500,
            display: 'flex',
            flexDirection: 'column',
            zIndex: 1001
          }}
        >
          <Box sx={{ p: 2, bgcolor: '#ff9800', color: 'white' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SupportAgent />
              <Typography variant="h6">Travel Assistant</Typography>
            </Box>
          </Box>

          <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
            {messages.map((msg, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                  mb: 2
                }}
              >
                {msg.sender === 'bot' && (
                  <Avatar sx={{ bgcolor: '#ff9800', mr: 1 }}>
                    <SupportAgent sx={{ fontSize: 20 }} />
                  </Avatar>
                )}
                <Paper
                  sx={{
                    p: 1.5,
                    maxWidth: '70%',
                    bgcolor: msg.sender === 'user' ? '#1976d2' : 'grey.100',
                    color: msg.sender === 'user' ? 'white' : 'text.primary'
                  }}
                >
                  {msg.sender === 'bot' ? (
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <Typography variant="body2" sx={{ mb: 1 }}>{children}</Typography>,
                        strong: ({ children }) => <strong style={{ fontWeight: 700 }}>{children}</strong>,
                        ul: ({ children }) => <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>{children}</ul>,
                        ol: ({ children }) => <ol style={{ margin: '8px 0', paddingLeft: '20px' }}>{children}</ol>,
                        li: ({ children }) => <li style={{ marginBottom: '4px' }}>{children}</li>
                      }}
                    >
                      {msg.text}
                    </ReactMarkdown>
                  ) : (
                    <Typography variant="body2">{msg.text}</Typography>
                  )}
                </Paper>
              </Box>
            ))}
            {loading && (
              <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
                <Avatar sx={{ bgcolor: '#ff9800', mr: 1 }}>
                  <SupportAgent sx={{ fontSize: 20 }} />
                </Avatar>
                <Paper sx={{ p: 1.5, bgcolor: 'grey.100' }}>
                  <Typography variant="body2">Typing...</Typography>
                </Paper>
              </Box>
            )}
            <div ref={messagesEndRef} />
          </Box>

          <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Ask me anything..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
            <IconButton 
              sx={{ 
                color: '#ff9800',
                '&:disabled': { color: 'grey.400' }
              }} 
              onClick={handleSend} 
              disabled={loading || !input.trim()}
            >
              <Send />
            </IconButton>
          </Box>
        </Paper>
      )}
    </>
  );
};

export default Chatbot;
