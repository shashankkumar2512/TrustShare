export default function FilterChips({ chips, activeId, onChange }) {
  return (
    <div className="my-files-chips">
      {chips.map((chip) => (
        <button
          key={chip.id}
          type="button"
          onClick={() => onChange(chip.id)}
          className={`my-files-chip ${chip.id === activeId ? 'is-active' : ''}`}
        >
          {chip.label}
        </button>
      ))}
    </div>
  );
}