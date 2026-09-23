import React from 'react';

/**
 * ButtonGroup component — renders a group of buttons in a horizontal row
 * @param {Array<{label: string, onClick: function, variant: string, disabled: boolean}>} buttons
 * @param {string} gap - Gap between buttons (default: '8px')
 */
const ButtonGroup = ({ buttons = [], gap = '8px' }) => {
  const getVariantStyle = (variant = 'primary') => {
    const base = {
      padding: '10px 20px',
      borderRadius: '8px',
      border: 'none',
      fontSize: '14px',
      fontWeight: 600,
      cursor: 'pointer',
      transition: 'all 0.2s ease',
    };
    const variants = {
      primary: { background: 'var(--primary)', color: '#fff' },
      secondary: { background: 'var(--surface)', color: 'var(--text)', border: '1px solid var(--border)' },
      danger: { background: 'var(--danger)', color: '#fff' },
      ghost: { background: 'transparent', color: 'var(--primary)', border: '1px solid var(--primary)' },
    };
    return { ...base, ...(variants[variant] || variants.primary) };
  };

  return (
    <div style={{ display: 'flex', gap, flexWrap: 'wrap', alignItems: 'center' }}>
      {buttons.map((btn, idx) => (
        <button
          key={idx}
          onClick={btn.onClick}
          disabled={btn.disabled}
          style={{
            ...getVariantStyle(btn.variant),
            opacity: btn.disabled ? 0.5 : 1,
            cursor: btn.disabled ? 'not-allowed' : 'pointer',
          }}
        >
          {btn.label}
        </button>
      ))}
    </div>
  );
};

export default ButtonGroup;
