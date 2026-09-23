import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

import Notifications, { getNotificationAction } from './Notifications';
import { notificationsAPI } from '../utils/api';

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

jest.mock('../utils/api', () => ({
  notificationsAPI: {
    list: jest.fn(),
    markRead: jest.fn(),
    markAllRead: jest.fn(),
    delete: jest.fn(),
  },
}));

const notifications = [
  {
    id: 1,
    type: 'share',
    category: 'shares',
    title: 'A file was shared with you',
    message: 'Priya shared "Roadmap.pdf" with you.',
    is_read: false,
    created_at: '2026-08-09T08:00:00Z',
  },
  {
    id: 2,
    type: 'security',
    category: 'security',
    title: 'New sign-in',
    message: 'A new browser signed in to your account.',
    is_read: true,
    created_at: '2026-08-09T08:05:00Z',
  },
];

beforeEach(() => {
  jest.clearAllMocks();
  notificationsAPI.list.mockResolvedValue({ data: notifications });
  notificationsAPI.markRead.mockResolvedValue({});
});

test('renders informative actor, action, target, time, and status content', async () => {
  render(<Notifications />);

  expect(await screen.findByText('Priya shared "Roadmap.pdf" with you.')).toBeInTheDocument();
  expect(screen.getByText('New sign-in')).toBeInTheDocument();
  expect(screen.getByLabelText('Unread')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Open shared files/i })).toBeInTheDocument();
});

test('marks an unread share notification read before opening the related resource', async () => {
  render(<Notifications />);

  userEvent.click(await screen.findByRole('button', { name: /Open shared files/i }));

  await waitFor(() => {
    expect(notificationsAPI.markRead).toHaveBeenCalledWith(1);
    expect(mockNavigate).toHaveBeenCalledWith('/shared-with-me');
  });
});

test('routes security notifications directly to the Security settings tab', async () => {
  render(<Notifications />);

  userEvent.click(await screen.findByRole('button', { name: /Review security/i }));

  expect(notificationsAPI.markRead).not.toHaveBeenCalledWith(2);
  expect(mockNavigate).toHaveBeenCalledWith('/settings?tab=security');
});

test('maps remaining notification types to useful destinations', () => {
  expect(getNotificationAction({ type: 'expiration' }).destination).toBe('/sharing');
  expect(getNotificationAction({ type: 'summary' }).destination).toBe('/my-files');
  expect(getNotificationAction({ type: 'download' }).destination).toBe('/activity');
});
