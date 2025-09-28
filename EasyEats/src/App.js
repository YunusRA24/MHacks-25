import React, { useState } from 'react';
import './App.css';

function App() {
  const [searchInput, setSearchInput] = useState('');
  const [showNotice, setShowNotice] = useState(false);
  const [backendMsg, setBackendMsg] = useState('');
  const [backendPretty, setBackendPretty] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    setShowNotice(true);
    setTimeout(() => setShowNotice(false), 6000);

    const text = searchInput;
    setSearchInput('');

    try {
      const resp = await fetch('http://127.0.0.1:5000/api/shop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await resp.json();
      const msg = data.summary || data.error || 'Received a response.';
      setBackendMsg(msg);
      setBackendPretty(typeof data.pretty === 'string' ? data.pretty : '');
      setTimeout(() => {
        setBackendMsg('');
        setBackendPretty('');
      }, 30000);
    } catch (err) {
      setBackendMsg('Failed to reach backend. Is the server running?');
      setBackendPretty('');
      setTimeout(() => {
        setBackendMsg('');
        setBackendPretty('');
      }, 30000);
    }
  };

  const foodImages = [
    { src: '/food_pics/burger download.png', alt: 'Burger' },
    { src: '/food_pics/cupcake_image.png', alt: 'Cupcake' },
    { src: '/food_pics/pie2_image.png', alt: 'Pie' },
    { src: '/food_pics/tacos_image.png', alt: 'Tacos' }
  ];

  return (
    <div className="App">
      {/* Navigation Bar */}
      <nav className="navbar">
        <div className="nav-container">
          <div className="nav-left">
            <span className="nav-item">Home</span>
          </div>
          <div className="nav-center">
            <span className="nav-item">Recipes</span>
            <span className="nav-item">Update Fridge</span>
          </div>
          <div className="nav-right">
            <span className="nav-item">Login</span>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="main-content">
        {/* Animated Food Images in Circle */}
        <div className="food-circle">
          {foodImages.map((food, index) => (
            <div
              key={index}
              className="food-item"
              style={{
                '--rotation': `${(index * 360) / foodImages.length}deg`,
                '--delay': `${index * 0.5}s`
              }}
            >
              <img src={food.src} alt={food.alt} className="food-image" />
            </div>
          ))}
        </div>

        <div className="hero-section">
          <h1 className="hero-title">Create Something Delicious</h1>
          
          <form className="search-form" onSubmit={handleSearch}>
            <div className="search-container">
              <input
                type="text"
                placeholder="What ingredients do you have?"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="search-input"
              />
              <button type="submit" className="search-button">
                <span className="arrow">→</span>
              </button>
            </div>
          </form>

          {showNotice && (
            <div className="notice">
              <span className="notice-icon" aria-hidden>✉️</span>
              <span className="notice-text">Please check your email for the recipe/Ingredients list</span>
            </div>
          )}

          {backendMsg && (
            <div className="notice" style={{ marginTop: '10px' }}>
              <span className="notice-icon" aria-hidden>🛒</span>
              <span className="notice-text">{backendMsg}</span>
            </div>
          )}

          {backendPretty && (
            <div className="notice" style={{ marginTop: '8px', whiteSpace: 'pre-wrap', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace' }}>
              {backendPretty}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
