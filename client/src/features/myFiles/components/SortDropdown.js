import { useEffect, useRef, useState } from 'react';
import { ArrowUpDown, Check, ChevronDown } from 'lucide-react';

export default function SortDropdown({ value, options, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    const handleKey = (e) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, []);

  const currentLabel = options.find((o) => o.id === value)?.label || 'Sort';

  return (
    <div className="my-files-sort" ref={ref}>
      <button
        type="button"
        className={`my-files-sort-btn ${open ? 'is-open' : ''}`}
        onClick={() => setOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <ArrowUpDown size={14} strokeWidth={2.2} />
        <span className="my-files-sort-label">{currentLabel}</span>
        <ChevronDown size={13} strokeWidth={2.4} className={`my-files-sort-chevron ${open ? 'is-open' : ''}`} />
      </button>

      {open && (
        <div className="my-files-sort-menu" role="listbox">
          {options.map((opt) => {
            const isActive = opt.id === value;
            return (
              <button
                key={opt.id}
                type="button"
                className={`my-files-sort-option ${isActive ? 'is-active' : ''}`}
                onClick={() => { onChange(opt.id); setOpen(false); }}
                role="option"
                aria-selected={isActive}
              >
                <span>{opt.label}</span>
                {isActive && <Check size={13} strokeWidth={2.6} />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}