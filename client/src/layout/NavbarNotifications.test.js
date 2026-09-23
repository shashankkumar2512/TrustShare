import { getUnreadNotificationPreview } from './Navbar';


test('bell preview includes only the newest unread notifications', () => {
  const notifications = [
    { id: 1, is_read: true },
    { id: 2, is_read: false },
    { id: 3, is_read: false },
    { id: 4, is_read: false },
    { id: 5, is_read: false },
    { id: 6, is_read: false },
    { id: 7, is_read: false },
  ];

  expect(getUnreadNotificationPreview(notifications).map((item) => item.id)).toEqual([
    2, 3, 4, 5, 6,
  ]);
});
