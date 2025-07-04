import React from 'react';

const SearchBox = ({ value, onChange, placeholder = "Search logs..." }) => {
  const handleChange = (e) => {
    onChange(e.target.value);
  };

  return (
    <div className="search-box-container">
      <input
        type="text"
        className="search-box"
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
      />
    </div>
  );
};

export default SearchBox;
