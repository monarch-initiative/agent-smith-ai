import React, { useState } from 'react';
import './App.css';

function App() {
  const [chatLog, setChatLog] = useState([]);
  const [question, setQuestion] = useState('');

  const handleChat = async () => {
    const response = await fetch('http://localhost:8000/chat/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question: "this is a test"})
    });
    const data = await response.json();
    setChatLog([...chatLog, ...data.responses]);
    setQuestion('');  // Clear the input after sending
  };

  return (
    <div className="App">
      <div className="chatWindow">
        {chatLog.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            {message.content}
          </div>
        ))}
      </div>
      <div className="chatInput">
        <input value={question} onChange={e => setQuestion(e.target.value)} placeholder="Type your message..."/>
        <button onClick={handleChat}>Send</button>
      </div>
    </div>
  );
}

export default App;
