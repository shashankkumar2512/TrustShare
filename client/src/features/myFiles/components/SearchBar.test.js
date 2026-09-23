import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

import SearchBar from './SearchBar';


test('shows a clear button only for a populated query and keeps one search icon', () => {
  const onChange = jest.fn();
  const onClear = jest.fn();
  const { container, rerender } = render(
    <SearchBar value="" onChange={onChange} onClear={onClear} />
  );

  expect(screen.queryByRole('button', { name: 'Clear file search' })).not.toBeInTheDocument();

  rerender(<SearchBar value="report" onChange={onChange} onClear={onClear} />);

  fireEvent.change(screen.getByRole('textbox', { name: 'Search files' }), { target: { value: 'budget' } });
  fireEvent.click(screen.getByRole('button', { name: 'Clear file search' }));

  expect(onChange).toHaveBeenCalledWith('budget');
  expect(onClear).toHaveBeenCalledTimes(1);
  expect(container.querySelectorAll('svg.lucide-search')).toHaveLength(1);
});
