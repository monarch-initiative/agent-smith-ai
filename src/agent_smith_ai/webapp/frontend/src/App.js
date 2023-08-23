import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import gfm from 'remark-gfm';
import './App.css';

function App() {
  const [chatLog, setChatLog] = useState([]);
  const [question, setQuestion] = useState('');
  const ws = useRef(null);

  const getWebSocketUrl = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws/chat/`;
  }

  const getLocalSessionId = () => {
    // If the user has a session id in local storage, use that.
    // Otherwise, generate a new session id and store it in local storage.
    if (!localStorage.getItem("sessionId")) { 
      localStorage.setItem("sessionId", Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)); 
    }
    return localStorage.getItem("sessionId");
  }

  useEffect(() => {
    ws.current = new WebSocket(getWebSocketUrl());

    ws.current.onopen = () => console.log("ws opened");
    ws.current.onmessage = (e) => {
        const messageData = JSON.parse(e.data);
        setChatLog((prevLog) => [...prevLog, messageData]);
    };
    ws.current.onclose = () => {
        console.log("ws closed");
        // Here you can implement logic to handle a reconnect if necessary.
    };

    return () => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.close();
        }
    };
  }, []);

  const handleChat = () => {
    const message = {
        question: question,
        session_id: getLocalSessionId()
    };

    if (ws.current.readyState !== WebSocket.OPEN) {
        console.error("WebSocket is not open. Can't send message.");
        // Optionally, you can implement logic here to handle a reconnect.
        return;
    }
    
    ws.current.send(JSON.stringify(message));
  };


  return (
    <div className="App">
      <div className="chatWindow">
        {chatLog.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            {message.is_function_call ? (
              <React.Fragment>
                <span>{message.func_name}</span>
                <span className="toggle-function">👁️</span> 
              </React.Fragment>
            ) : (
              <ReactMarkdown>{message.content}</ReactMarkdown>
            )}
          </div>
        ))}
      </div>
      <div className="chatInput">
        <input 
          value={question} 
          onChange={e => setQuestion(e.target.value)} 
          placeholder="Type your message..."
        />
        <button onClick={handleChat}>Send</button>
      </div>
    </div>
  );
  
}

export default App;
