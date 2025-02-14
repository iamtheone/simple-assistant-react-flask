import React, { useState } from 'react';

function App() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setResponse('');

    const eventSource = new EventSource(
      `http://localhost:5000/chat?message=${encodeURIComponent(message)}`
    );

    eventSource.onmessage = (event) => {
      setResponse((prev) => prev + event.data);
    };

    eventSource.onerror = () => {
      eventSource.close();
      setIsLoading(false);
    };
  };

  return (
    <div className="container mx-auto p-4">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="border p-2 w-full mb-4"
        />
        <button 
          type="submit"
          disabled={isLoading}
          className="bg-blue-500 text-white px-4 py-2 rounded"
        >
          Send
        </button>
      </form>
      <div className="mt-4 whitespace-pre-wrap">
        {response}
      </div>
    </div>
  );
}

export default App;
