import { COOKIE_NAME } from "@shared/const";
import { z } from "zod";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, protectedProcedure, router } from "./_core/trpc";
import { invokeLLM } from "./_core/llm";
import { generateImage } from "./_core/imageGeneration";
import { storagePut } from "./storage";
import { nanoid } from "nanoid";
import * as db from "./db";

// Helper to generate pedagogical visual based on type
async function generateVisual(questionText: string, visualType: string) {
  let prompt = "";

  switch (visualType) {
    case "flowchart":
      prompt = `Create a CLEAR, PEDAGOGICAL flowchart diagram for geotechnical engineering students.

Topic: ${questionText}

Requirements:
- Show step-by-step process flow with clear arrows
- Use simple, rectangular boxes for steps and diamond shapes for decisions
- Include clear labels on each step (keep text concise)
- Use a clean, professional color scheme (blues/grays)
- Add decision points with "Yes/No" or clear criteria
- Ensure logical flow from top to bottom or left to right
- Make it easy to follow for students learning this concept
- Include a title at the top

Style: Clean, modern, educational diagram with high readability`;
      break;
    case "diagram":
      prompt = `Create a CLEAR, PEDAGOGICAL technical diagram for geotechnical engineering students.

Topic: ${questionText}

Requirements:
- Show all key components and their relationships
- Use clear labels for each element
- Draw connection lines to show relationships
- Use a professional color scheme to differentiate element types
- Include dimensions or measurements where relevant
- Add a legend if needed for symbols/colors
- Make it anatomically or structurally accurate
- Ensure high educational value and clarity
- Include a descriptive title

Style: Technical illustration with clear labels, professional appearance, educational focus`;
      break;
    case "infographic":
      prompt = `Create a CLEAR, PEDAGOGICAL infographic for geotechnical engineering students.

Topic: ${questionText}

Requirements:
- Present key facts, statistics, and data visually
- Use charts, graphs, or icons to represent information
- Include clear headings and section divisions
- Use a vibrant but professional color palette
- Make numbers and statistics prominent and easy to read
- Add visual hierarchy (larger = more important)
- Include comparisons or trends where applicable
- Balance text with visuals (more visual, less text)
- Ensure information is accurate and educational
- Add a clear title and subtitle

Style: Modern infographic with data visualization, engaging and informative`;
      break;
    case "illustration":
      prompt = `Create a CLEAR, PEDAGOGICAL technical illustration for geotechnical engineering students.

Topic: ${questionText}

Requirements:
- Show cross-sections, layers, or structural details
- Use realistic but simplified representation
- Include clear labels pointing to important features
- Show depth, dimension, or scale references
- Use appropriate colors (soil browns, rock grays, water blues, etc.)
- Add hatching or patterns to differentiate materials
- Make abstract concepts visually concrete
- Include annotation arrows or callouts
- Show both overview and detailed sections if needed
- Add a descriptive title

Style: Technical illustration with cross-sectional view, educational detail, professional quality`;
      break;
    default:
      prompt = `Create a clear, educational technical diagram for this geotechnical engineering concept: ${questionText}. Make it pedagogical and easy for students to understand.`;
  }

  const { url } = await generateImage({ prompt });
  return url;
}

export const appRouter = router({
  system: systemRouter,
  auth: router({
    me: publicProcedure.query((opts) => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  // Q&A Router
  qa: router({
    ask: publicProcedure
      .input(
        z.object({
          questionText: z.string().min(10, "Question must be at least 10 characters"),
          includeVisual: z.boolean(),
          visualType: z.enum(["flowchart", "diagram", "infographic", "illustration"]).optional(),
        })
      )
      .mutation(async ({ input, ctx }) => {
        // Create question record (use userId 0 for guest users)
        const userId = ctx.user?.id ?? 0;
        let questionId: number | null = null;
        let dbAvailable = true;

        try {
          questionId = await db.createQuestion({
            userId,
            questionText: input.questionText,
            includeVisual: input.includeVisual,
            visualType: input.visualType,
          });
        } catch (dbError) {
          console.warn("[Q&A] Database unavailable, operating in stateless mode:", dbError);
          dbAvailable = false;
        }

        // Generate AI answer with visual-type-specific instructions
        let systemPrompt = "You are an expert geotechnical engineering professor. Provide detailed, accurate, and pedagogically sound explanations to student questions. Use clear language, include relevant formulas when appropriate, and explain concepts step-by-step. Format your response in markdown.";

        // Add visual-type-specific pedagogical instructions
        if (input.includeVisual && input.visualType) {
          switch (input.visualType) {
            case "flowchart":
              systemPrompt += "\n\nIMPORTANT: Your explanation will be accompanied by a process flowchart. Structure your response to complement the flowchart by:\n- Describing each step in the process sequentially\n- Clearly identifying decision points and their criteria\n- Explaining the logic flow and transitions between steps\n- Using numbered steps or clear section headings to match the flowchart structure";
              break;
            case "diagram":
              systemPrompt += "\n\nIMPORTANT: Your explanation will be accompanied by a technical diagram. Structure your response to complement the diagram by:\n- Identifying and explaining each component shown in the diagram\n- Describing relationships and connections between elements\n- Using clear labels and references to diagram parts\n- Explaining how components interact within the system";
              break;
            case "infographic":
              systemPrompt += "\n\nIMPORTANT: Your explanation will be accompanied by an educational infographic. Structure your response to complement the infographic by:\n- Presenting key facts and statistics clearly\n- Using bullet points for important data points\n- Organizing information into digestible sections\n- Highlighting comparisons, trends, or patterns in the data";
              break;
            case "illustration":
              systemPrompt += "\n\nIMPORTANT: Your explanation will be accompanied by a technical illustration. Structure your response to complement the illustration by:\n- Describing visual elements and their significance\n- Explaining layers, cross-sections, or structural details\n- Using spatial language (top, bottom, left, right, above, below)\n- Relating abstract concepts to concrete visual representations";
              break;
          }
        }


        // Try to use Python Brain first, fallback to simple LLM
        let answerText: string;
        let usedPythonBrain = false;

        try {
          // Import Python Brain client
          const { askPythonBrain, checkPythonBrainHealth } = await import("./_core/pythonBrain");

          // Check if Python Brain is available
          const brainHealthy = await checkPythonBrainHealth();

          if (brainHealthy) {
            console.log("[Brain] Using Python multi-agent brain system");

            const brainResponse = await askPythonBrain({
              question: input.questionText,
              includeVisual: input.includeVisual,
              visualType: input.visualType,
            });

            // Use the critique (final reviewed answer) from the multi-agent system
            answerText = brainResponse.critique || brainResponse.answer;
            usedPythonBrain = true;

            console.log("[Brain] Successfully got response from Python brain");
          } else {
            throw new Error("Python Brain health check failed");
          }
        } catch (brainError) {
          console.warn("[Brain] Python Brain unavailable, falling back to simple LLM:", brainError);

          // Fallback to simple LLM call
          const response = await invokeLLM({
            messages: [
              {
                role: "system",
                content: systemPrompt,
              },
              {
                role: "user",
                content: input.questionText,
              },
            ],
          });

          const messageContent = response.choices[0]?.message?.content;
          answerText = typeof messageContent === "string" ? messageContent : "Unable to generate answer at this time.";
        }

        // Generate visual if requested
        let visualUrl: string | undefined;
        let visualKey: string | undefined;

        if (input.includeVisual && input.visualType) {
          try {
            visualUrl = await generateVisual(input.questionText, input.visualType);
            visualKey = `visuals/${userId}/${nanoid()}.png`;
          } catch (error) {
            console.error("Failed to generate visual:", error);
          }
        }

        // Save answer (only if database is available)
        let answerId: number | null = null;
        if (dbAvailable && questionId !== null) {
          try {
            answerId = await db.createAnswer({
              questionId,
              answerText,
              visualUrl,
              visualKey,
            });
          } catch (dbError) {
            console.warn("[Q&A] Failed to save answer to database:", dbError);
          }
        }

        return {
          questionId: questionId ?? -1,
          answerId: answerId ?? -1,
          answerText,
          visualUrl,
        };
      }),

    getHistory: protectedProcedure.query(async ({ ctx }) => {
      const questions = await db.getUserQuestions(ctx.user.id);

      // Get answers for each question
      const questionsWithAnswers = await Promise.all(
        questions.map(async (q) => {
          const answer = await db.getAnswerByQuestionId(q.id);
          return {
            ...q,
            answer,
          };
        })
      );

      return questionsWithAnswers;
    }),

    getQuestionWithAnswer: protectedProcedure.input(z.object({ questionId: z.number() })).query(async ({ input }) => {
      const question = await db.getQuestionById(input.questionId);
      const answer = await db.getAnswerByQuestionId(input.questionId);

      return {
        question,
        answer,
      };
    }),
  }),

  // Library Router
  library: router({
    save: protectedProcedure
      .input(
        z.object({
          questionId: z.number(),
          tags: z.string().optional(),
          notes: z.string().optional(),
        })
      )
      .mutation(async ({ input, ctx }) => {
        const id = await db.saveContent({
          userId: ctx.user.id,
          questionId: input.questionId,
          tags: input.tags,
          notes: input.notes,
        });

        return { id };
      }),

    getSaved: protectedProcedure.query(async ({ ctx }) => {
      return await db.getUserSavedContent(ctx.user.id);
    }),

    delete: protectedProcedure.input(z.object({ id: z.number() })).mutation(async ({ input, ctx }) => {
      await db.deleteSavedContent(input.id, ctx.user.id);
      return { success: true };
    }),
  }),

  // Modules Router
  modules: router({
    list: publicProcedure.query(async () => {
      return await db.getAllModules();
    }),

    get: publicProcedure.input(z.object({ id: z.number() })).query(async ({ input }) => {
      return await db.getModuleById(input.id);
    }),

    getProgress: protectedProcedure.query(async ({ ctx }) => {
      return await db.getUserModuleProgress(ctx.user.id);
    }),

    updateProgress: protectedProcedure
      .input(
        z.object({
          moduleId: z.number(),
          progressPercent: z.number().min(0).max(100),
          completed: z.boolean(),
        })
      )
      .mutation(async ({ input, ctx }) => {
        await db.upsertModuleProgress({
          userId: ctx.user.id,
          moduleId: input.moduleId,
          progressPercent: input.progressPercent,
          completed: input.completed,
          completedAt: input.completed ? new Date() : undefined,
        });

        return { success: true };
      }),
  }),

  // Classroom Router (Teacher features)
  classroom: router({
    create: protectedProcedure
      .input(
        z.object({
          name: z.string().min(1),
          description: z.string().optional(),
        })
      )
      .mutation(async ({ input, ctx }) => {
        const inviteCode = nanoid(10);

        const id = await db.createClassroom({
          teacherId: ctx.user.id,
          name: input.name,
          description: input.description,
          inviteCode,
        });

        return { id, inviteCode };
      }),

    getMyClassrooms: protectedProcedure.query(async ({ ctx }) => {
      if (ctx.user.role === "teacher" || ctx.user.role === "admin") {
        return await db.getTeacherClassrooms(ctx.user.id);
      } else {
        return await db.getStudentClassrooms(ctx.user.id);
      }
    }),

    get: protectedProcedure.input(z.object({ id: z.number() })).query(async ({ input }) => {
      return await db.getClassroomById(input.id);
    }),

    enroll: protectedProcedure.input(z.object({ inviteCode: z.string() })).mutation(async ({ input, ctx }) => {
      const classroom = await db.getClassroomByInviteCode(input.inviteCode);

      if (!classroom) {
        throw new Error("Invalid invite code");
      }

      const id = await db.enrollStudent({
        classroomId: classroom.id,
        studentId: ctx.user.id,
      });

      return { id, classroom };
    }),

    getStudents: protectedProcedure.input(z.object({ classroomId: z.number() })).query(async ({ input }) => {
      return await db.getClassroomStudents(input.classroomId);
    }),

    createAssignment: protectedProcedure
      .input(
        z.object({
          classroomId: z.number(),
          title: z.string(),
          description: z.string().optional(),
          assignmentType: z.enum(["question", "module"]),
          referenceId: z.number().optional(),
          dueDate: z.date().optional(),
        })
      )
      .mutation(async ({ input }) => {
        const id = await db.createAssignment(input);
        return { id };
      }),

    getAssignments: protectedProcedure.input(z.object({ classroomId: z.number() })).query(async ({ input }) => {
      return await db.getClassroomAssignments(input.classroomId);
    }),

    getMyAssignments: protectedProcedure.query(async ({ ctx }) => {
      return await db.getStudentAssignments(ctx.user.id);
    }),
  }),

  // Document Generation Router
  documents: router({
    generateExamSheet: protectedProcedure
      .input(
        z.object({
          questionId: z.number(),
          title: z.string(),
          numQuestions: z.number().min(1).max(20).optional(),
        })
      )
      .mutation(async ({ input, ctx }) => {
        const question = await db.getQuestionById(input.questionId);
        const answer = await db.getAnswerByQuestionId(input.questionId);

        if (!question || !answer) {
          throw new Error("Question or answer not found");
        }

        const examContent = await invokeLLM({
          messages: [
            {
              role: "system",
              content: "You are an expert geotechnical engineering professor creating exam questions.",
            },
            {
              role: "user",
              content: `Create an exam sheet with ${input.numQuestions || 5} questions about: ${question.questionText}`,
            },
          ],
        });

        const examText = typeof examContent.choices[0]?.message.content === "string"
          ? examContent.choices[0].message.content
          : JSON.stringify(examContent.choices[0]?.message.content || "");
        const fileKey = `documents/${ctx.user.id}/exam-${nanoid()}.md`;
        const { url } = await storagePut(fileKey, examText, "text/markdown");

        const docId = await db.createGeneratedDocument({
          userId: ctx.user.id,
          questionId: input.questionId,
          documentType: "exam_sheet",
          title: input.title,
          documentUrl: url,
          documentKey: fileKey,
        });

        return { docId, url, title: input.title };
      }),

    generateSlides: protectedProcedure
      .input(
        z.object({
          questionId: z.number(),
          title: z.string(),
          numSlides: z.number().min(3).max(15).optional(),
        })
      )
      .mutation(async ({ input, ctx }) => {
        if (ctx.user.role !== "teacher" && ctx.user.role !== "admin") {
          throw new Error("Only teachers can generate slides");
        }

        const question = await db.getQuestionById(input.questionId);
        const answer = await db.getAnswerByQuestionId(input.questionId);

        if (!question || !answer) {
          throw new Error("Question or answer not found");
        }

        const slidesContent = await invokeLLM({
          messages: [
            {
              role: "system",
              content: "You are an expert at creating educational presentations.",
            },
            {
              role: "user",
              content: `Create a presentation with ${input.numSlides || 8} slides about: ${question.questionText}`,
            },
          ],
        });

        const slidesText = typeof slidesContent.choices[0]?.message.content === "string"
          ? slidesContent.choices[0].message.content
          : JSON.stringify(slidesContent.choices[0]?.message.content || "");
        const fileKey = `documents/${ctx.user.id}/slides-${nanoid()}.md`;
        const { url } = await storagePut(fileKey, slidesText, "text/markdown");

        const docId = await db.createGeneratedDocument({
          userId: ctx.user.id,
          questionId: input.questionId,
          documentType: "presentation_slides",
          title: input.title,
          documentUrl: url,
          documentKey: fileKey,
        });

        return { docId, url, title: input.title };
      }),

    list: protectedProcedure.query(async ({ ctx }) => {
      return await db.getUserGeneratedDocuments(ctx.user.id);
    }),

    delete: protectedProcedure
      .input(z.object({ id: z.number() }))
      .mutation(async ({ input, ctx }) => {
        await db.deleteGeneratedDocument(input.id, ctx.user.id);
        return { success: true };
      }),
  }),

  // Learning Projects Router
  projects: router({
    create: protectedProcedure
      .input(
        z.object({
          title: z.string().min(1, "Title is required"),
          description: z.string().optional(),
          initialContext: z.string().optional(),
          objectives: z.array(z.string()).optional(),
          color: z.string().regex(/^#[0-9A-F]{6}$/i).optional(),
        })
      )
      .mutation(async ({ input, ctx }) => {
        const projectId = await db.createLearningProject({
          userId: ctx.user.id,
          title: input.title,
          description: input.description,
          initialContext: input.initialContext,
          objectives: input.objectives ? JSON.stringify(input.objectives) : undefined,
          color: input.color,
        });

        // Create initial project context
        await db.getOrCreateProjectContext(projectId, ctx.user.id);

        return { projectId };
      }),

    list: protectedProcedure.query(async ({ ctx }) => {
      return await db.getUserLearningProjects(ctx.user.id);
    }),

    get: protectedProcedure
      .input(z.object({ id: z.number() }))
      .query(async ({ input, ctx }) => {
        const project = await db.getLearningProjectById(input.id);
        if (!project || project.userId !== ctx.user.id) {
          throw new Error("Project not found");
        }
        return project;
      }),

    update: protectedProcedure
      .input(
        z.object({
          id: z.number(),
          title: z.string().optional(),
          description: z.string().optional(),
          objectives: z.array(z.string()).optional(),
          isActive: z.boolean().optional(),
        })
      )
      .mutation(async ({ input, ctx }) => {
        const project = await db.getLearningProjectById(input.id);
        if (!project || project.userId !== ctx.user.id) {
          throw new Error("Project not found");
        }

        await db.updateLearningProject(input.id, {
          title: input.title,
          description: input.description,
          objectives: input.objectives ? JSON.stringify(input.objectives) : undefined,
          isActive: input.isActive,
        });

        return { success: true };
      }),

    delete: protectedProcedure
      .input(z.object({ id: z.number() }))
      .mutation(async ({ input, ctx }) => {
        const project = await db.getLearningProjectById(input.id);
        if (!project || project.userId !== ctx.user.id) {
          throw new Error("Project not found");
        }

        await db.deleteLearningProject(input.id);
        return { success: true };
      }),

    getContext: protectedProcedure
      .input(z.object({ projectId: z.number() }))
      .query(async ({ input, ctx }) => {
        const project = await db.getLearningProjectById(input.projectId);
        if (!project || project.userId !== ctx.user.id) {
          throw new Error("Project not found");
        }
        return await db.getOrCreateProjectContext(input.projectId, ctx.user.id);
      }),

    updateContext: protectedProcedure
      .input(
        z.object({
          projectId: z.number(),
          contextData: z.record(z.string(), z.any()),
        })
      )
      .mutation(async ({ input, ctx }) => {
        const project = await db.getLearningProjectById(input.projectId);
        if (!project || project.userId !== ctx.user.id) {
          throw new Error("Project not found");
        }

        await db.updateProjectContext(input.projectId, ctx.user.id, input.contextData);
        return { success: true };
      }),

    addQuestion: protectedProcedure
      .input(
        z.object({
          projectId: z.number(),
          questionId: z.number(),
        })
      )
      .mutation(async ({ input, ctx }) => {
        const project = await db.getLearningProjectById(input.projectId);
        if (!project || project.userId !== ctx.user.id) {
          throw new Error("Project not found");
        }

        await db.addQuestionToProject(input.projectId, input.questionId);
        return { success: true };
      }),

    getQuestions: protectedProcedure
      .input(z.object({ projectId: z.number() }))
      .query(async ({ input, ctx }) => {
        const project = await db.getLearningProjectById(input.projectId);
        if (!project || project.userId !== ctx.user.id) {
          throw new Error("Project not found");
        }
        return await db.getProjectQuestions(input.projectId);
      }),

    removeQuestion: protectedProcedure
      .input(
        z.object({
          projectId: z.number(),
          questionId: z.number(),
        })
      )
      .mutation(async ({ input, ctx }) => {
        const project = await db.getLearningProjectById(input.projectId);
        if (!project || project.userId !== ctx.user.id) {
          throw new Error("Project not found");
        }

        await db.removeQuestionFromProject(input.projectId, input.questionId);
        return { success: true };
      }),
  }),

  // Workspace Router (Collaborative features)
  workspace: router({
    create: protectedProcedure
      .input(
        z.object({
          name: z.string(),
          classroomId: z.number().optional(),
        })
      )
      .mutation(async ({ input, ctx }) => {
        const id = await db.createWorkspace({
          name: input.name,
          createdBy: ctx.user.id,
          content: JSON.stringify({ elements: [] }),
          classroomId: input.classroomId,
        });

        return { id };
      }),

    list: protectedProcedure.query(async ({ ctx }) => {
      return await db.getUserWorkspaces(ctx.user.id);
    }),

    get: protectedProcedure.input(z.object({ id: z.number() })).query(async ({ input }) => {
      return await db.getWorkspaceById(input.id);
    }),

    updateContent: protectedProcedure
      .input(
        z.object({
          id: z.number(),
          content: z.string(),
        })
      )
      .mutation(async ({ input }) => {
        await db.updateWorkspaceContent(input.id, input.content);
        return { success: true };
      }),
  }),
});

export type AppRouter = typeof appRouter;
