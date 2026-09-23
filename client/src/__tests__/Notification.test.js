import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';

// Mock Notification Component for unit testing
const NotificationItem = ({ title, isRead, onMarkRead }) => (
  <div data-testid="notification-item">
    <span>{title}</span>
    {!isRead && <button onClick={onMarkRead}>Mark as Read</button>}
  </div>
);

describe('Notification Module Unit Tests', () => {
  
  // Test Case 1: Renders notification title properly
  test('renders notification title correctly', () => {
    render(<NotificationItem title="Failed login attempt detected" isRead={false} />);
    const titleElement = screen.getByText('Failed login attempt detected');
    expect(titleElement).toBeTruthy();
  });

  // Test Case 2: Clicking "Mark as Read" calls the callback handler
  test('triggers mark as read handler on button click', () => {
    const handleMarkRead = jest.fn();
    render(<NotificationItem title="File shared with you" isRead={false} onMarkRead={handleMarkRead} />);
    
    const button = screen.getByText('Mark as Read');
    fireEvent.click(button);
    
    expect(handleMarkRead).toHaveBeenCalledTimes(1);
  });
});