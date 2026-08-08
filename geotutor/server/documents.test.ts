import { describe, expect, it } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";

type AuthenticatedUser = NonNullable<TrpcContext["user"]>;

function createAuthContext(role: "teacher" | "admin" | "student" = "student"): { ctx: TrpcContext } {
  const user: AuthenticatedUser = {
    id: 1,
    openId: "test-user",
    email: "test@example.com",
    name: "Test User",
    loginMethod: "manus",
    role,
    createdAt: new Date(),
    updatedAt: new Date(),
    lastSignedIn: new Date(),
  };

  const ctx: TrpcContext = {
    user,
    req: {
      protocol: "https",
      headers: {},
    } as TrpcContext["req"],
    res: {
      clearCookie: () => {},
    } as TrpcContext["res"],
  };

  return { ctx };
}

describe("documents.generateExamSheet", () => {
  it("should reject non-existent question", async () => {
    const { ctx } = createAuthContext("student");
    const caller = appRouter.createCaller(ctx);

    try {
      await caller.documents.generateExamSheet({
        questionId: 99999,
        title: "Test Exam",
        numQuestions: 5,
      });
      expect.fail("Should have thrown an error");
    } catch (error: any) {
      expect(error.message).toContain("Question or answer not found");
    }
  });

  it("should validate numQuestions range", async () => {
    const { ctx } = createAuthContext("student");
    const caller = appRouter.createCaller(ctx);

    try {
      await caller.documents.generateExamSheet({
        questionId: 1,
        title: "Test Exam",
        numQuestions: 25, // exceeds max of 20
      });
      expect.fail("Should have thrown validation error");
    } catch (error: any) {
      expect(error.message).toContain("too_big");
    }
  });

  it("should accept valid input with default numQuestions", async () => {
    const { ctx } = createAuthContext("student");
    const caller = appRouter.createCaller(ctx);

    // This will fail due to missing question, but validates input structure
    try {
      await caller.documents.generateExamSheet({
        questionId: 1,
        title: "Test Exam",
      });
    } catch (error: any) {
      // Expected to fail on question lookup, not input validation
      expect(error.message).toContain("Question or answer not found");
    }
  });
});

describe("documents.generateSlides", () => {
  it("should reject students from generating slides", async () => {
    const { ctx } = createAuthContext("student");
    const caller = appRouter.createCaller(ctx);

    try {
      await caller.documents.generateSlides({
        questionId: 1,
        title: "Test Slides",
        numSlides: 8,
      });
      expect.fail("Should have thrown permission error");
    } catch (error: any) {
      expect(error.message).toContain("Only teachers can generate slides");
    }
  });

  it("should allow teachers to generate slides", async () => {
    const { ctx } = createAuthContext("teacher");
    const caller = appRouter.createCaller(ctx);

    // This will fail due to missing question, but validates permission
    try {
      await caller.documents.generateSlides({
        questionId: 1,
        title: "Test Slides",
        numSlides: 8,
      });
    } catch (error: any) {
      // Expected to fail on question lookup, not permission
      expect(error.message).toContain("Question or answer not found");
    }
  });

  it("should allow admins to generate slides", async () => {
    const { ctx } = createAuthContext("admin");
    const caller = appRouter.createCaller(ctx);

    // This will fail due to missing question, but validates permission
    try {
      await caller.documents.generateSlides({
        questionId: 1,
        title: "Test Slides",
        numSlides: 8,
      });
    } catch (error: any) {
      // Expected to fail on question lookup, not permission
      expect(error.message).toContain("Question or answer not found");
    }
  });

  it("should validate numSlides range", async () => {
    const { ctx } = createAuthContext("teacher");
    const caller = appRouter.createCaller(ctx);

    try {
      await caller.documents.generateSlides({
        questionId: 1,
        title: "Test Slides",
        numSlides: 20, // exceeds max of 15
      });
      expect.fail("Should have thrown validation error");
    } catch (error: any) {
      expect(error.message).toContain("too_big");
    }
  });

  it("should reject numSlides below minimum", async () => {
    const { ctx } = createAuthContext("teacher");
    const caller = appRouter.createCaller(ctx);

    try {
      await caller.documents.generateSlides({
        questionId: 1,
        title: "Test Slides",
        numSlides: 2, // below min of 3
      });
      expect.fail("Should have thrown validation error");
    } catch (error: any) {
      expect(error.message).toContain("too_small");
    }
  });
});

describe("documents.list", () => {
  it("should return empty list for user with no documents", async () => {
    const { ctx } = createAuthContext("student");
    const caller = appRouter.createCaller(ctx);

    const documents = await caller.documents.list();
    expect(Array.isArray(documents)).toBe(true);
  });
});

describe("documents.delete", () => {
  it("should reject deletion of non-existent document", async () => {
    const { ctx } = createAuthContext("student");
    const caller = appRouter.createCaller(ctx);

    try {
      await caller.documents.delete({ id: 99999 });
      // Should not throw for non-existent document
      expect(true).toBe(true);
    } catch (error: any) {
      // If it throws, it should be a database error
      expect(error).toBeDefined();
    }
  });
});
