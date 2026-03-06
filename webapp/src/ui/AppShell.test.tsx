import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { appRouter } from "../routes";

describe("AppShell", () => {
  it("renders control center shell", () => {
    const router = createMemoryRouter(appRouter.routes, {
      initialEntries: ["/"],
    });

    render(<RouterProvider router={router} />);

    expect(screen.getByText("Operations Control Center")).toBeInTheDocument();
    expect(screen.getByText("Window")).toBeInTheDocument();
    expect(screen.getByText("Service")).toBeInTheDocument();
    expect(screen.getByText("Loading live operations view...")).toBeInTheDocument();
  });
});
