import React from 'react';

/**
 * RadioButton component
 * @param {string} id - Radio input ID
 * @param {string} name - Radio group name
 * @param {string} label - Radio label text
 * @param {string} value - Radio value
 * @param {string} checked - Currently selected value
 * @param {function} onChange - Change handler
 * @param {boolean} disabled - Disabled state
 */
const RadioButton = ({ id, name, label, value, checked, onChange, disabled = false }) => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '6px 0' }}>
      <input
        type="radio"
        id={id}
        name={name}
        value={value}
        checked={checked === value}
        onChange={onChange}
        disabled={disabled}
        style={{ width: '16px', height: '16px', cursor: disabled ? 'not-allowed' : 'pointer', accentColor: 'var(--primary)' }}
      />
      {label && (
        <label htmlFor={id} style={{ cursor: disabled ? 'not-allowed' : 'pointer', color: disabled ? 'var(--text-muted)' : 'var(--text)' }}>
          {label}
        </label>
      )}
    </div>
  );
};

export default RadioButton;
