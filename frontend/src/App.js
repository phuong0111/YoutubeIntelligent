import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ChannelsPage from './pages/ChannelsPage';
import VideosPage from './pages/VideosPage';
import TasksPage from './pages/TasksPage';
import ChannelPage from './pages/ChannelPage';
import VideoPage from './pages/VideoPage';
import { FaYoutube, FaChartBar } from 'react-icons/fa';
import './index.css';

const Header = () => (
  <header className="app-header">
    <div className="header-content">
      <div className="logo">
        <FaYoutube className="logo-icon" size={24} />
        <span>YouTube Content Analysis</span>
      </div>
      <nav>
        <ul>
          <li><NavLink to="/" end>Dashboard</NavLink></li>
          <li><NavLink to="/channels">Channels</NavLink></li>
          <li><NavLink to="/videos">Videos</NavLink></li>
          <li><NavLink to="/tasks">Tasks</NavLink></li>
        </ul>
      </nav>
    </div>
  </header>
);

const App = () => {
  return (
    <BrowserRouter>
      <div className="app">
        <Header />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/channels" element={<ChannelsPage />} />
            <Route path="/channels/:id" element={<ChannelPage />} />
            <Route path="/videos" element={<VideosPage />} />
            <Route path="/videos/:id" element={<VideoPage />} />
            <Route path="/tasks" element={<TasksPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;