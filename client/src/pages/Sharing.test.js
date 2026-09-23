import { getShareStatus } from './Sharing';


test('classifies public share lifecycle states consistently', () => {
  const now = new Date('2026-08-09T12:00:00Z');

  expect(getShareStatus({ is_active: false }, now)).toBe('revoked');
  expect(getShareStatus({ is_active: true, expires_at: '2026-08-09T11:59:00Z' }, now)).toBe('expired');
  expect(getShareStatus({ is_active: true, max_views: 2, access_count: 2 }, now)).toBe('limit-reached');
  expect(getShareStatus({ is_active: true, max_views: 2, access_count: 1 }, now)).toBe('active');
});
