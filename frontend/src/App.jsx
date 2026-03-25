import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ChatProvider } from './context/ChatContext';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { TitilerTestWindow } from './components/TitilerTestWindow';

function App() {
  return (
    <BrowserRouter>
      <ChatProvider>
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <Routes>
            <Route path="/" element={<ChatArea />} />
            <Route path="/test-map" element={<TitilerTestWindow />} />
          </Routes>
        </div>
      </ChatProvider>
    </BrowserRouter>
  );
}

export default App;
