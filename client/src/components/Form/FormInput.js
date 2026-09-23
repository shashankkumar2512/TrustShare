import React from 'react';

/**
 * FormInput component
 * @param {string} id - Input ID
 * @param {string} label - Label text
 * @param {string} type - Input type (text, email, password, etc.)
 * @param {string} value - Controlled value
 * @param {function} onChange - Change handler
 * @param {string} placeholder - Placeholder text
 * @param {string} error - Error message
 * @param {boolean} required - Required flag
 * @param {boolean} disabled - Disabled state
 */
const FormInput = ({
  id,
  label,
  type = 'text',
  value,
  onChange,
  placeholder = '',
  error = '',
  required = false,
  disabled = false,
}) => {
  const inputStyle = {
    width: '100%',
    padding: '10px 14px',
    borderRadius: '8px',
    border: `1px solid ${error ? 'var(--danger)' : 'var(--border)'}`,
    background: 'var(--surface)',
    color: 'var(--text)',
    fontSize: '14px',
    outline: 'none',
    transition: 'border-color 0.2s',
  };

  return (
    <div style={{ marginBottom: '16px' }}>
      {label && (
        <label htmlFor={id} style={{ display: 'block', marginBottom: '6px', fontSize: '14px', fontWeight: 500 }}>
          {label} {required && <span style={{ color: 'var(--danger)' }}>*</span>}
        </label>
      )}
      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        style={inputStyle}
      />
      {error && <p style={{ color: 'var(--danger)', fontSize: '12px', marginTop: '4px' }}>{error}</p>}
    </div>
  );
};

export default FormInput;
