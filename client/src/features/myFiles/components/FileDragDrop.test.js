import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

import FileCard from './FileCard';
import FolderCard from './FolderCard';


test('file cards expose the file id and name while dragging', () => {
  const dataTransfer = { effectAllowed: '', setData: jest.fn() };
  const { container } = render(
    <FileCard file={{ id: 42, original_name: 'report.pdf', size: 10, encrypted: true }} />
  );
  const card = container.querySelector('article');

  expect(card).toHaveAttribute('draggable', 'true');
  fireEvent.dragStart(card, { dataTransfer });

  expect(dataTransfer.effectAllowed).toBe('move');
  expect(dataTransfer.setData).toHaveBeenCalledWith(
    'application/x-trustshare-file',
    JSON.stringify({ id: 42, name: 'report.pdf' })
  );
  expect(card).toHaveClass('opacity-60');
  fireEvent.dragEnd(card);
  expect(card).not.toHaveClass('opacity-60');
});


test('folder cards highlight and pass the dropped file without opening the folder', () => {
  const onFileDrop = jest.fn();
  const onOpen = jest.fn();
  const dataTransfer = {
    dropEffect: '',
    getData: jest.fn(() => JSON.stringify({ id: 42, name: 'report.pdf' })),
  };
  const { container } = render(
    <FolderCard
      id={7}
      title="Evidence"
      subtitle="0 items"
      onFileDrop={onFileDrop}
      onOpen={onOpen}
    />
  );
  const folder = screen.getByRole('button', { name: /Evidence/i });

  fireEvent.dragOver(folder, { dataTransfer });
  expect(container.querySelector('article')).toHaveClass('my-files-folder--drop-target');

  fireEvent.drop(folder, { dataTransfer });
  expect(onFileDrop).toHaveBeenCalledWith(
    { id: 7, name: 'Evidence' },
    { id: 42, name: 'report.pdf' }
  );
  expect(onOpen).not.toHaveBeenCalled();
  expect(container.querySelector('article')).not.toHaveClass('my-files-folder--drop-target');
});


test('pointer dragging moves a file without opening the target folder', () => {
  const onFileDrop = jest.fn();
  const onOpen = jest.fn();
  const draggedFile = { id: 42, name: 'report.pdf' };
  const { container } = render(
    <FolderCard
      id={7}
      title="Evidence"
      subtitle="0 items"
      onFileDrop={onFileDrop}
      onOpen={onOpen}
      pointerDraggedFile={draggedFile}
    />
  );
  const folder = screen.getByRole('button', { name: /Evidence/i });

  fireEvent.pointerEnter(folder);
  expect(container.querySelector('article')).toHaveClass('my-files-folder--drop-target');

  fireEvent.pointerUp(folder);
  expect(onFileDrop).toHaveBeenCalledWith({ id: 7, name: 'Evidence' }, draggedFile);
  expect(onOpen).not.toHaveBeenCalled();
  expect(container.querySelector('article')).not.toHaveClass('my-files-folder--drop-target');
});
