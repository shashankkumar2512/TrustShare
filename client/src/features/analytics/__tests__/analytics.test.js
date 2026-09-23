// client/src/features/analytics/__tests__/analytics.test.js
/**
 * Unit tests for Analytics Module Components.
 * 5 comprehensive tests covering rendering, props, and behavior.
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import EmptyState from "../components/shared/EmptyState";
import Skeleton from "../components/shared/Skeleton";


// ══════════════════════════════════════════════════════════════════════
//  TEST 1: EmptyState Renders Custom Message
// ══════════════════════════════════════════════════════════════════════
describe("EmptyState Component", () => {
  test("renders with custom message prop", () => {
    // Arrange: Define custom message
    const customMessage = "No analytics data available yet";
    
    // Act: Render component with the message
    render(<EmptyState message={customMessage} />);
    
    // Assert: Message should appear on screen
    const messageElement = screen.getByText(customMessage);
    expect(messageElement).toBeInTheDocument();
    
    console.log("✅ TEST 1 PASSED: EmptyState displays custom message");
  });
});


// ══════════════════════════════════════════════════════════════════════
//  TEST 2: EmptyState Uses Default Message When No Prop
// ══════════════════════════════════════════════════════════════════════
describe("EmptyState Default Behavior", () => {
  test("renders with default message when no message prop provided", () => {
    // Act: Render component WITHOUT any props
    render(<EmptyState />);
    
    // Assert: Default message should be shown
    const defaultText = screen.getByText(/No data available/i);
    expect(defaultText).toBeInTheDocument();
    
    console.log("✅ TEST 2 PASSED: EmptyState shows default message");
  });
});


// ══════════════════════════════════════════════════════════════════════
//  TEST 3: Skeleton Renders with Correct CSS Class
// ══════════════════════════════════════════════════════════════════════
describe("Skeleton Component", () => {
  test("renders with correct base CSS class", () => {
    // Act: Render Skeleton component
    const { container } = render(<Skeleton />);
    
    // Assert: Should have the 'an-skeleton' base class
    const skeletonElement = container.querySelector(".an-skeleton");
    expect(skeletonElement).toBeInTheDocument();
    expect(skeletonElement).toHaveClass("an-skeleton");
    
    console.log("✅ TEST 3 PASSED: Skeleton has correct base class");
  });
});


// ══════════════════════════════════════════════════════════════════════
//  TEST 4: Skeleton Accepts Custom CSS Class
// ══════════════════════════════════════════════════════════════════════
describe("Skeleton Custom Class", () => {
  test("accepts and applies additional custom className", () => {
    // Arrange: Custom class to add
    const customClass = "an-skeleton--icon";
    
    // Act: Render with custom class
    const { container } = render(<Skeleton className={customClass} />);
    
    // Assert: Should have BOTH base class and custom class
    const skeletonElement = container.querySelector(".an-skeleton");
    expect(skeletonElement).toHaveClass("an-skeleton");
    expect(skeletonElement).toHaveClass(customClass);
    
    console.log("✅ TEST 4 PASSED: Skeleton accepts custom className");
  });
});


// ══════════════════════════════════════════════════════════════════════
//  TEST 5: Skeleton Applies Custom Inline Styles
// ══════════════════════════════════════════════════════════════════════
describe("Skeleton Custom Styles", () => {
  test("applies custom inline styles from props", () => {
    // Arrange: Custom styles
    const customStyle = { 
      width: "150px", 
      height: "30px" 
    };
    
    // Act: Render with custom styles
    const { container } = render(<Skeleton style={customStyle} />);
    
    // Assert: Styles should be applied
    const skeletonElement = container.querySelector(".an-skeleton");
    expect(skeletonElement).toBeInTheDocument();
    expect(skeletonElement).toHaveStyle("width: 150px");
    expect(skeletonElement).toHaveStyle("height: 30px");
    
    console.log("✅ TEST 5 PASSED: Skeleton applies custom inline styles");
  });
});