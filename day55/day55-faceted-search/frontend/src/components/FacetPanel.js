import React from 'react';

const FacetPanel = ({ facets, selectedFilters, onFilterChange }) => {
  const handleFacetValueToggle = (facetName, value) => {
    const currentValues = selectedFilters[facetName] || [];
    const newValues = currentValues.includes(value)
      ? currentValues.filter(v => v !== value)
      : [...currentValues, value];
    
    onFilterChange(facetName, newValues);
  };

  if (!facets || facets.length === 0) {
    return <div className="loading">Loading filters...</div>;
  }

  return (
    <div className="facet-panel">
      {facets.map((facet) => (
        <div key={facet.name} className="facet-group">
          <div className="facet-title">{facet.display_name}</div>
          {facet.values.slice(0, 10).map((facetValue) => (
            <div
              key={facetValue.value}
              className={`facet-value ${facetValue.selected ? 'selected' : ''}`}
              onClick={() => handleFacetValueToggle(facet.name, facetValue.value)}
            >
              <input
                type="checkbox"
                className="facet-checkbox"
                checked={facetValue.selected}
                onChange={() => {}} // Handled by onClick above
              />
              <span className="facet-label">{facetValue.value}</span>
              <span className="facet-count">{facetValue.count}</span>
            </div>
          ))}
          {facet.values.length > 10 && (
            <div className="facet-more">
              +{facet.values.length - 10} more
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default FacetPanel;
