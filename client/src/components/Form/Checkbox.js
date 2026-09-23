import React from 'react';

/**
 * Checkbox component
 * @param {string} id - Unique identifier
 * @param {string} label - Checkbox label text
 * @param {boolean} checked - Controlled checked state
 * @param {function} onChange - Change handler
 * @param {boolean} disabled - Disabled state
 */
const Checkbox = ({ id, label, checked = false, onChange, disabled = false }) => {
  return (
    <div className="checkbox-wrapper" style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '6px 0' }}>
      <input
        type="checkbox"
        id={id}
        checked={checked}
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

export default Checkbox;
