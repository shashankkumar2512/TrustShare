import React from 'react';

/**
 * FormSelect component
 * @param {string} id - Select ID
 * @param {string} label - Label text
 * @param {string} value - Controlled value
 * @param {function} onChange - Change handler
 * @param {Array<{value: string, label: string}>} options - Select options
 * @param {string} placeholder - Default empty option text
 * @param {string} error - Error message
 * @param {boolean} required - Required flag
 * @param {boolean} disabled - Disabled state
 */
const FormSelect = ({
  id,
  label,
  value,
  onChange,
  options = [],
  placeholder = 'Select an option',
  error = '',
  required = false,
  disabled = false,
}) => {
  const selectStyle = {
    width: '100%',
    padding: '10px 14px',
    borderRadius: '8px',
    border: `1px solid ${error ? 'var(--danger)' : 'var(--border)'}`,
    background: 'var(--surface)',
    color: 'var(--text)',
    fontSize: '14px',
    outline: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
  };

  return (
    <div style={{ marginBottom: '16px' }}>
      {label && (
        <label htmlFor={id} style={{ display: 'block', marginBottom: '6px', fontSize: '14px', fontWeight: 500 }}>
          {label} {required && <span style={{ color: 'var(--danger)' }}>*</span>}
        </label>
      )}
      <select id={id} value={value} onChange={onChange} required={required} disabled={disabled} style={selectStyle}>
        <option value="" disabled>
          {placeholder}
        </option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p style={{ color: 'var(--danger)', fontSize: '12px', marginTop: '4px' }}>{error}</p>}
    </div>
  );
};

export default FormSelect;
