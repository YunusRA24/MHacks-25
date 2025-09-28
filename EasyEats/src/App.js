import React, { useState } from 'react';
import './App.css';

function App() {
  const [searchInput, setSearchInput] = useState('');
  const [showNotice, setShowNotice] = useState(false);

  const handleSearch = (e) => {
    e.preventDefault();
    // Trigger notice
    setShowNotice(true);
    // Hide after 6 seconds (a few more seconds)
    setTimeout(() => setShowNotice(false), 6000);
    // Clear the chatbox
    setSearchInput('');
    // You can also handle your actual search/submit logic here
    console.log('Searching for:', searchInput);
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
        </div>
      </div>
    </div>
  );
}

export default App;
