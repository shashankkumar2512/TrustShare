import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import ActivityPage from "./ActivityPage";
import { getActivities } from "./activityService";

jest.mock("./activityService", () => ({ getActivities: jest.fn() }));

describe("ActivityPage", () => {
  beforeEach(() => {
    getActivities.mockResolvedValue([
      {
        id: 1,
        user_id: 7,
        action: "UPLOAD",
        resource_type: "file",
        resource_name: "security-report.pdf",
        level: "info",
        created_at: "2026-07-29T08:30:00Z",
      },
    ]);
  });

  afterEach(() => jest.clearAllMocks());

  test("loads and renders the authenticated user's real activity", async () => {
    render(<ActivityPage />);

    expect(screen.getByText(/loading your secure activity trail/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("security-report.pdf")).toBeInTheDocument());
    expect(getActivities).toHaveBeenCalledWith();
    expect(screen.getAllByText("Upload").length).toBeGreaterThan(0);
  });

  test("does not expose sample activity or arbitrary user controls", async () => {
    render(<ActivityPage />);
    await waitFor(() => expect(screen.getByText("security-report.pdf")).toBeInTheDocument());

    expect(screen.queryByText(/add sample/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/user id/i)).not.toBeInTheDocument();
  });
});
