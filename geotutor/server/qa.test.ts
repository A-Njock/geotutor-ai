import { describe, expect, it, vi, beforeEach } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";
import * as db from "./db";
import * as llm from "./_core/llm";
import * as imageGen from "./_core/imageGeneration";

// Mock dependencies
vi.mock("./db");
vi.mock("./_core/llm");
vi.mock("./_core/imageGeneration");

type AuthenticatedUser = NonNullable<TrpcContext["user"]>;

function createAuthContext(userId: number = 1, role: "student" | "teacher" | "admin" = "student"): TrpcContext {
  const user: AuthenticatedUser = {
    id: userId,
    openId: `test-user-${userId}`,
    email: `user${userId}@example.com`,
    name: `Test User ${userId}`,
    loginMethod: "manus",
    role,
    createdAt: new Date(),
    updatedAt: new Date(),
    lastSignedIn: new Date(),
  };

  return {
    user,
    req: {
      protocol: "https",
      headers: {},
    } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

describe("Q&A Router", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("qa.ask", () => {
    it("should create question and generate text-only answer", async () => {
      const ctx = createAuthContext();
      const caller = appRouter.createCaller(ctx);

      // Mock database calls
      vi.mocked(db.createQuestion).mockResolvedValue(1);
      vi.mocked(db.createAnswer).mockResolvedValue(1);

      // Mock LLM response
      vi.mocked(llm.invokeLLM).mockResolvedValue({
        choices: [
          {
            message: {
              content: "This is a detailed answer about bearing capacity...",
              role: "assistant",
            },
            finish_reason: "stop",
            index: 0,
          },
        ],
        id: "test-id",
        model: "test-model",
        object: "chat.completion",
        created: Date.now(),
      });

      const result = await caller.qa.ask({
        questionText: "What is bearing capacity?",
        includeVisual: false,
      });

      expect(result.questionId).toBe(1);
      expect(result.answerId).toBe(1);
      expect(result.answerText).toContain("bearing capacity");
      expect(result.visualUrl).toBeUndefined();

      expect(db.createQuestion).toHaveBeenCalledWith({
        userId: 1,
        questionText: "What is bearing capacity?",
        includeVisual: false,
        visualType: undefined,
      });

      expect(llm.invokeLLM).toHaveBeenCalled();
      expect(db.createAnswer).toHaveBeenCalled();
    });

    it("should generate visual when requested", async () => {
      const ctx = createAuthContext();
      const caller = appRouter.createCaller(ctx);

      vi.mocked(db.createQuestion).mockResolvedValue(2);
      vi.mocked(db.createAnswer).mockResolvedValue(2);

      vi.mocked(llm.invokeLLM).mockResolvedValue({
        choices: [
          {
            message: {
              content: "Explanation of soil classification...",
              role: "assistant",
            },
            finish_reason: "stop",
            index: 0,
          },
        ],
        id: "test-id",
        model: "test-model",
        object: "chat.completion",
        created: Date.now(),
      });

      vi.mocked(imageGen.generateImage).mockResolvedValue({
        url: "https://example.com/diagram.png",
      });

      const result = await caller.qa.ask({
        questionText: "Explain soil classification",
        includeVisual: true,
        visualType: "diagram",
      });

      expect(result.visualUrl).toBe("https://example.com/diagram.png");
      expect(imageGen.generateImage).toHaveBeenCalled();

      const imageGenCall = vi.mocked(imageGen.generateImage).mock.calls[0][0];
      expect(imageGenCall.prompt).toContain("diagram");
      expect(imageGenCall.prompt).toContain("soil classification");
    });

    it("should reject questions shorter than 10 characters", async () => {
      const ctx = createAuthContext();
      const caller = appRouter.createCaller(ctx);

      await expect(
        caller.qa.ask({
          questionText: "Short",
          includeVisual: false,
        })
      ).rejects.toThrow();
    });

    it("should handle LLM errors gracefully", async () => {
      const ctx = createAuthContext();
      const caller = appRouter.createCaller(ctx);

      vi.mocked(db.createQuestion).mockResolvedValue(3);
      vi.mocked(llm.invokeLLM).mockRejectedValue(new Error("LLM service unavailable"));

      await expect(
        caller.qa.ask({
          questionText: "What is consolidation?",
          includeVisual: false,
        })
      ).rejects.toThrow("LLM service unavailable");
    });
  });

  describe("qa.getHistory", () => {
    it("should return user's question history with answers", async () => {
      const ctx = createAuthContext();
      const caller = appRouter.createCaller(ctx);

      const mockQuestions = [
        {
          id: 1,
          userId: 1,
          questionText: "What is bearing capacity?",
          includeVisual: false,
          visualType: null,
          createdAt: new Date(),
        },
        {
          id: 2,
          userId: 1,
          questionText: "Explain soil classification",
          includeVisual: true,
          visualType: "diagram" as const,
          createdAt: new Date(),
        },
      ];

      const mockAnswer = {
        id: 1,
        questionId: 1,
        answerText: "Bearing capacity is...",
        visualUrl: null,
        visualKey: null,
        createdAt: new Date(),
      };

      vi.mocked(db.getUserQuestions).mockResolvedValue(mockQuestions);
      vi.mocked(db.getAnswerByQuestionId).mockResolvedValue(mockAnswer);

      const result = await caller.qa.getHistory();

      expect(result).toHaveLength(2);
      expect(result[0].questionText).toBe("What is bearing capacity?");
      expect(result[0].answer).toBeDefined();
      expect(db.getUserQuestions).toHaveBeenCalledWith(1);
    });

    it("should return empty array for users with no history", async () => {
      const ctx = createAuthContext(2);
      const caller = appRouter.createCaller(ctx);

      vi.mocked(db.getUserQuestions).mockResolvedValue([]);

      const result = await caller.qa.getHistory();

      expect(result).toEqual([]);
    });
  });

  describe("qa.getQuestionWithAnswer", () => {
    it("should return specific question and answer", async () => {
      const ctx = createAuthContext();
      const caller = appRouter.createCaller(ctx);

      const mockQuestion = {
        id: 1,
        userId: 1,
        questionText: "What is bearing capacity?",
        includeVisual: false,
        visualType: null,
        createdAt: new Date(),
      };

      const mockAnswer = {
        id: 1,
        questionId: 1,
        answerText: "Bearing capacity is the maximum load...",
        visualUrl: null,
        visualKey: null,
        createdAt: new Date(),
      };

      vi.mocked(db.getQuestionById).mockResolvedValue(mockQuestion);
      vi.mocked(db.getAnswerByQuestionId).mockResolvedValue(mockAnswer);

      const result = await caller.qa.getQuestionWithAnswer({ questionId: 1 });

      expect(result.question).toEqual(mockQuestion);
      expect(result.answer).toEqual(mockAnswer);
    });
  });
});
