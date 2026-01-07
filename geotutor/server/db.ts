import { eq, desc, and, sql } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import {
  InsertUser,
  users,
  questions,
  InsertQuestion,
  answers,
  InsertAnswer,
  savedContent,
  InsertSavedContent,
  modules,
  InsertModule,
  moduleProgress,
  InsertModuleProgress,
  classrooms,
  InsertClassroom,
  classroomStudents,
  InsertClassroomStudent,
  assignments,
  InsertAssignment,
  assignmentSubmissions,
  InsertAssignmentSubmission,
  workspaces,
  InsertWorkspace,
  workspaceParticipants,
  InsertWorkspaceParticipant,
  generatedDocuments,
  InsertGeneratedDocument,
  learningProjects,
  InsertLearningProject,
  projectContexts,
  InsertProjectContext,
  projectQuestions,
  InsertProjectQuestion,
} from "../drizzle/schema";
import { ENV } from "./_core/env";

let _db: ReturnType<typeof drizzle> | null = null;

export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

// ==================== USER OPERATIONS ====================

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = "admin";
      updateSet.role = "admin";
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);
  return result.length > 0 ? result[0] : undefined;
}

// ==================== QUESTION OPERATIONS ====================

export async function createQuestion(question: InsertQuestion) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.insert(questions).values(question);
  return result[0].insertId;
}

export async function getQuestionById(id: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.select().from(questions).where(eq(questions.id, id)).limit(1);
  return result[0];
}

export async function getUserQuestions(userId: number, limit: number = 50) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db
    .select()
    .from(questions)
    .where(eq(questions.userId, userId))
    .orderBy(desc(questions.createdAt))
    .limit(limit);
}

// ==================== ANSWER OPERATIONS ====================

export async function createAnswer(answer: InsertAnswer) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.insert(answers).values(answer);
  return result[0].insertId;
}

export async function getAnswerByQuestionId(questionId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.select().from(answers).where(eq(answers.questionId, questionId)).limit(1);
  return result[0];
}

// ==================== SAVED CONTENT OPERATIONS ====================

export async function saveContent(content: InsertSavedContent) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.insert(savedContent).values(content);
  return result[0].insertId;
}

export async function getUserSavedContent(userId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db
    .select({
      id: savedContent.id,
      questionId: savedContent.questionId,
      tags: savedContent.tags,
      notes: savedContent.notes,
      savedAt: savedContent.savedAt,
      questionText: questions.questionText,
      includeVisual: questions.includeVisual,
      visualType: questions.visualType,
      answerText: answers.answerText,
      visualUrl: answers.visualUrl,
    })
    .from(savedContent)
    .leftJoin(questions, eq(savedContent.questionId, questions.id))
    .leftJoin(answers, eq(questions.id, answers.questionId))
    .where(eq(savedContent.userId, userId))
    .orderBy(desc(savedContent.savedAt));
}

export async function deleteSavedContent(id: number, userId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db.delete(savedContent).where(and(eq(savedContent.id, id), eq(savedContent.userId, userId)));
}

// ==================== MODULE OPERATIONS ====================

export async function getAllModules() {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.select().from(modules).orderBy(modules.difficulty, modules.title);
}

export async function getModuleById(id: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.select().from(modules).where(eq(modules.id, id)).limit(1);
  return result[0];
}

export async function createModule(module: InsertModule) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.insert(modules).values(module);
  return result[0].insertId;
}

// ==================== MODULE PROGRESS OPERATIONS ====================

export async function getUserModuleProgress(userId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db
    .select({
      id: moduleProgress.id,
      moduleId: moduleProgress.moduleId,
      completed: moduleProgress.completed,
      progressPercent: moduleProgress.progressPercent,
      lastAccessedAt: moduleProgress.lastAccessedAt,
      completedAt: moduleProgress.completedAt,
      moduleTitle: modules.title,
      moduleDifficulty: modules.difficulty,
      estimatedMinutes: modules.estimatedMinutes,
    })
    .from(moduleProgress)
    .leftJoin(modules, eq(moduleProgress.moduleId, modules.id))
    .where(eq(moduleProgress.userId, userId))
    .orderBy(desc(moduleProgress.lastAccessedAt));
}

export async function upsertModuleProgress(progress: InsertModuleProgress) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db
    .insert(moduleProgress)
    .values(progress)
    .onDuplicateKeyUpdate({
      set: {
        progressPercent: progress.progressPercent,
        completed: progress.completed,
        lastAccessedAt: new Date(),
        completedAt: progress.completedAt,
      },
    });
}

// ==================== CLASSROOM OPERATIONS ====================

export async function createClassroom(classroom: InsertClassroom) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.insert(classrooms).values(classroom);
  return result[0].insertId;
}

export async function getTeacherClassrooms(teacherId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.select().from(classrooms).where(eq(classrooms.teacherId, teacherId));
}

export async function getClassroomById(id: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.select().from(classrooms).where(eq(classrooms.id, id)).limit(1);
  return result[0];
}

export async function getClassroomByInviteCode(inviteCode: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.select().from(classrooms).where(eq(classrooms.inviteCode, inviteCode)).limit(1);
  return result[0];
}

// ==================== CLASSROOM STUDENT OPERATIONS ====================

export async function enrollStudent(enrollment: InsertClassroomStudent) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.insert(classroomStudents).values(enrollment);
  return result[0].insertId;
}

export async function getClassroomStudents(classroomId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db
    .select({
      id: classroomStudents.id,
      studentId: classroomStudents.studentId,
      enrolledAt: classroomStudents.enrolledAt,
      studentName: users.name,
      studentEmail: users.email,
    })
    .from(classroomStudents)
    .leftJoin(users, eq(classroomStudents.studentId, users.id))
    .where(eq(classroomStudents.classroomId, classroomId));
}

export async function getStudentClassrooms(studentId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db
    .select({
      id: classrooms.id,
      name: classrooms.name,
      description: classrooms.description,
      teacherId: classrooms.teacherId,
      enrolledAt: classroomStudents.enrolledAt,
    })
    .from(classroomStudents)
    .leftJoin(classrooms, eq(classroomStudents.classroomId, classrooms.id))
    .where(eq(classroomStudents.studentId, studentId));
}

// ==================== ASSIGNMENT OPERATIONS ====================

export async function createAssignment(assignment: InsertAssignment) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.insert(assignments).values(assignment);
  return result[0].insertId;
}

export async function getClassroomAssignments(classroomId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.select().from(assignments).where(eq(assignments.classroomId, classroomId)).orderBy(desc(assignments.createdAt));
}

export async function getStudentAssignments(studentId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db
    .select({
      assignmentId: assignments.id,
      title: assignments.title,
      description: assignments.description,
      assignmentType: assignments.assignmentType,
      referenceId: assignments.referenceId,
      dueDate: assignments.dueDate,
      classroomName: classrooms.name,
      completed: assignmentSubmissions.completed,
      submittedAt: assignmentSubmissions.submittedAt,
    })
    .from(classroomStudents)
    .leftJoin(assignments, eq(classroomStudents.classroomId, assignments.classroomId))
    .leftJoin(classrooms, eq(classroomStudents.classroomId, classrooms.id))
    .leftJoin(
      assignmentSubmissions,
      and(eq(assignments.id, assignmentSubmissions.assignmentId), eq(assignmentSubmissions.studentId, studentId))
    )
    .where(eq(classroomStudents.studentId, studentId))
    .orderBy(desc(assignments.createdAt));
}

// ==================== WORKSPACE OPERATIONS ====================

export async function createWorkspace(workspace: InsertWorkspace) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.insert(workspaces).values(workspace);
  return result[0].insertId;
}

export async function getUserWorkspaces(userId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db
    .select({
      id: workspaces.id,
      name: workspaces.name,
      createdBy: workspaces.createdBy,
      classroomId: workspaces.classroomId,
      createdAt: workspaces.createdAt,
      updatedAt: workspaces.updatedAt,
      role: workspaceParticipants.role,
    })
    .from(workspaceParticipants)
    .leftJoin(workspaces, eq(workspaceParticipants.workspaceId, workspaces.id))
    .where(eq(workspaceParticipants.userId, userId))
    .orderBy(desc(workspaces.updatedAt));
}

export async function getWorkspaceById(id: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.select().from(workspaces).where(eq(workspaces.id, id)).limit(1);
  return result[0];
}

export async function updateWorkspaceContent(id: number, content: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db.update(workspaces).set({ content, updatedAt: new Date() }).where(eq(workspaces.id, id));
}

// ==================== GENERATED DOCUMENTS OPERATIONS ====================

export async function createGeneratedDocument(doc: InsertGeneratedDocument) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.insert(generatedDocuments).values(doc);
  return result[0].insertId;
}

export async function getUserGeneratedDocuments(userId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db
    .select()
    .from(generatedDocuments)
    .where(eq(generatedDocuments.userId, userId))
    .orderBy(desc(generatedDocuments.createdAt));
}

export async function getGeneratedDocumentsByQuestion(questionId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db
    .select()
    .from(generatedDocuments)
    .where(eq(generatedDocuments.questionId, questionId))
    .orderBy(desc(generatedDocuments.createdAt));
}

export async function deleteGeneratedDocument(id: number, userId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db
    .delete(generatedDocuments)
    .where(and(eq(generatedDocuments.id, id), eq(generatedDocuments.userId, userId)));
}


// ==================== LEARNING PROJECTS OPERATIONS ====================

export async function createLearningProject(project: InsertLearningProject) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.insert(learningProjects).values(project);
  return result[0].insertId;
}

export async function getUserLearningProjects(userId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db
    .select()
    .from(learningProjects)
    .where(eq(learningProjects.userId, userId))
    .orderBy(desc(learningProjects.createdAt));
}

export async function getLearningProjectById(id: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db
    .select()
    .from(learningProjects)
    .where(eq(learningProjects.id, id))
    .limit(1);

  return result.length > 0 ? result[0] : undefined;
}

export async function updateLearningProject(id: number, updates: Partial<InsertLearningProject>) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db
    .update(learningProjects)
    .set({ ...updates, updatedAt: new Date() })
    .where(eq(learningProjects.id, id));
}

export async function deleteLearningProject(id: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db.delete(learningProjects).where(eq(learningProjects.id, id));
}

// ==================== PROJECT CONTEXT OPERATIONS ====================

export async function getOrCreateProjectContext(projectId: number, userId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const existing = await db
    .select()
    .from(projectContexts)
    .where(and(eq(projectContexts.projectId, projectId), eq(projectContexts.userId, userId)))
    .limit(1);

  if (existing.length > 0) {
    return existing[0];
  }

  const result = await db.insert(projectContexts).values({
    projectId,
    userId,
    contextData: JSON.stringify({ topics: [], learningPath: [] }),
  });

  return await db
    .select()
    .from(projectContexts)
    .where(eq(projectContexts.id, result[0].insertId))
    .limit(1)
    .then((rows) => rows[0]);
}

export async function updateProjectContext(projectId: number, userId: number, contextData: any) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db
    .update(projectContexts)
    .set({ contextData: JSON.stringify(contextData) })
    .where(and(eq(projectContexts.projectId, projectId), eq(projectContexts.userId, userId)));
}

// ==================== PROJECT QUESTIONS OPERATIONS ====================

export async function addQuestionToProject(projectId: number, questionId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.insert(projectQuestions).values({
    projectId,
    questionId,
  });

  return result[0].insertId;
}

export async function getProjectQuestions(projectId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db
    .select()
    .from(projectQuestions)
    .where(eq(projectQuestions.projectId, projectId))
    .orderBy(desc(projectQuestions.addedAt));
}

export async function removeQuestionFromProject(projectId: number, questionId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  await db
    .delete(projectQuestions)
    .where(and(eq(projectQuestions.projectId, projectId), eq(projectQuestions.questionId, questionId)));
}
