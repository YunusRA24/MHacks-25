import React, { useState } from 'react';
import './App.css';

function App() {
  const [searchInput, setSearchInput] = useState('');
  const [showNotice, setShowNotice] = useState(false);
  const [backendMsg, setBackendMsg] = useState('');
  const [backendDetails, setBackendDetails] = useState([]);

  const handleSearch = async (e) => {
    e.preventDefault();
    // Trigger notice
    setShowNotice(true);
    // Hide notice after 6 seconds
    setTimeout(() => setShowNotice(false), 6000);

    const text = searchInput;
    // Clear the chatbox
    setSearchInput('');

    // Call backend
    try {
      const resp = await fetch('http://127.0.0.1:5000/api/shop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await resp.json();
      const msg = data.summary || data.error || 'Received a response.';
      setBackendMsg(msg);
      setBackendDetails(Array.isArray(data.products) ? data.products : []);
      // Clear after 30 seconds
      setTimeout(() => {
        setBackendMsg('');
        setBackendDetails([]);
      }, 30000);
    } catch (err) {
      setBackendMsg('Failed to reach backend. Is the server running?');
      setBackendDetails([]);
      setTimeout(() => {
        setBackendMsg('');
        setBackendDetails([]);
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

          {backendDetails.length > 0 && (
            <div className="notice notice-list" style={{ marginTop: '8px' }}>
              <ul>
                {backendDetails.map((p, idx) => (
                  <li key={idx}>
                    {p.ingredient ? (<strong>{p.ingredient}</strong>) : null}
                    {typeof p.price === 'number' ? ` — $${p.price.toFixed(2)}` : ''}
                    {p.description ? ` — ${p.description}` : ''}
                    {p.error ? ` — ${p.error}` : ''}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
