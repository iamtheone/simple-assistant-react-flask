import { Chat } from '../components/Chat';

function App() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto p-4">
          <h1 className="text-2xl font-bold">AI Chat Assistant</h1>
        </div>
      </header>
      <main>
        <Chat />
      </main>
    </div>
  );
}

export default App;
