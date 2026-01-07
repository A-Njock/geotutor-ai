import { int, mysqlEnum, mysqlTable, text, timestamp, varchar, boolean, bigint } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 */
export const users = mysqlTable("users", {
  id: int("id").autoincrement().primaryKey(),
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin", "teacher", "student"]).default("student").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * Questions asked by users
 */
export const questions = mysqlTable("questions", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  questionText: text("questionText").notNull(),
  includeVisual: boolean("includeVisual").default(false).notNull(),
  visualType: mysqlEnum("visualType", ["flowchart", "diagram", "infographic", "illustration"]),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type Question = typeof questions.$inferSelect;
export type InsertQuestion = typeof questions.$inferInsert;

/**
 * AI-generated answers to questions
 */
export const answers = mysqlTable("answers", {
  id: int("id").autoincrement().primaryKey(),
  questionId: int("questionId").notNull(),
  answerText: text("answerText").notNull(),
  visualUrl: text("visualUrl"),
  visualKey: text("visualKey"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type Answer = typeof answers.$inferSelect;
export type InsertAnswer = typeof answers.$inferInsert;

/**
 * User's saved content library
 */
export const savedContent = mysqlTable("savedContent", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  questionId: int("questionId").notNull(),
  tags: text("tags"), // JSON array of tags
  notes: text("notes"),
  savedAt: timestamp("savedAt").defaultNow().notNull(),
});

export type SavedContent = typeof savedContent.$inferSelect;
export type InsertSavedContent = typeof savedContent.$inferInsert;

/**
 * Interactive learning modules
 */
export const modules = mysqlTable("modules", {
  id: int("id").autoincrement().primaryKey(),
  title: varchar("title", { length: 255 }).notNull(),
  description: text("description").notNull(),
  content: text("content").notNull(), // JSON content structure
  difficulty: mysqlEnum("difficulty", ["beginner", "intermediate", "advanced"]).notNull(),
  estimatedMinutes: int("estimatedMinutes").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Module = typeof modules.$inferSelect;
export type InsertModule = typeof modules.$inferInsert;

/**
 * User progress through learning modules
 */
export const moduleProgress = mysqlTable("moduleProgress", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  moduleId: int("moduleId").notNull(),
  completed: boolean("completed").default(false).notNull(),
  progressPercent: int("progressPercent").default(0).notNull(),
  lastAccessedAt: timestamp("lastAccessedAt").defaultNow().notNull(),
  completedAt: timestamp("completedAt"),
});

export type ModuleProgress = typeof moduleProgress.$inferSelect;
export type InsertModuleProgress = typeof moduleProgress.$inferInsert;

/**
 * Virtual classrooms created by teachers
 */
export const classrooms = mysqlTable("classrooms", {
  id: int("id").autoincrement().primaryKey(),
  teacherId: int("teacherId").notNull(),
  name: varchar("name", { length: 255 }).notNull(),
  description: text("description"),
  inviteCode: varchar("inviteCode", { length: 32 }).notNull().unique(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Classroom = typeof classrooms.$inferSelect;
export type InsertClassroom = typeof classrooms.$inferInsert;

/**
 * Students enrolled in classrooms
 */
export const classroomStudents = mysqlTable("classroomStudents", {
  id: int("id").autoincrement().primaryKey(),
  classroomId: int("classroomId").notNull(),
  studentId: int("studentId").notNull(),
  enrolledAt: timestamp("enrolledAt").defaultNow().notNull(),
});

export type ClassroomStudent = typeof classroomStudents.$inferSelect;
export type InsertClassroomStudent = typeof classroomStudents.$inferInsert;

/**
 * Assignments created by teachers
 */
export const assignments = mysqlTable("assignments", {
  id: int("id").autoincrement().primaryKey(),
  classroomId: int("classroomId").notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  description: text("description"),
  assignmentType: mysqlEnum("assignmentType", ["question", "module"]).notNull(),
  referenceId: int("referenceId"), // questionId or moduleId
  dueDate: timestamp("dueDate"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type Assignment = typeof assignments.$inferSelect;
export type InsertAssignment = typeof assignments.$inferInsert;

/**
 * Student assignment submissions
 */
export const assignmentSubmissions = mysqlTable("assignmentSubmissions", {
  id: int("id").autoincrement().primaryKey(),
  assignmentId: int("assignmentId").notNull(),
  studentId: int("studentId").notNull(),
  completed: boolean("completed").default(false).notNull(),
  submittedAt: timestamp("submittedAt"),
});

export type AssignmentSubmission = typeof assignmentSubmissions.$inferSelect;
export type InsertAssignmentSubmission = typeof assignmentSubmissions.$inferInsert;

/**
 * Collaborative workspaces
 */
export const workspaces = mysqlTable("workspaces", {
  id: int("id").autoincrement().primaryKey(),
  name: varchar("name", { length: 255 }).notNull(),
  createdBy: int("createdBy").notNull(),
  content: text("content").notNull(), // JSON diagram/notes content
  classroomId: int("classroomId"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Workspace = typeof workspaces.$inferSelect;
export type InsertWorkspace = typeof workspaces.$inferInsert;

/**
 * Workspace participants
 */
export const workspaceParticipants = mysqlTable("workspaceParticipants", {
  id: int("id").autoincrement().primaryKey(),
  workspaceId: int("workspaceId").notNull(),
  userId: int("userId").notNull(),
  role: mysqlEnum("role", ["owner", "editor", "viewer"]).default("editor").notNull(),
  joinedAt: timestamp("joinedAt").defaultNow().notNull(),
});

export type WorkspaceParticipant = typeof workspaceParticipants.$inferSelect;
export type InsertWorkspaceParticipant = typeof workspaceParticipants.$inferInsert;

/**
 * Generated documents (exam sheets, presentation slides)
 */
export const generatedDocuments = mysqlTable("generatedDocuments", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  questionId: int("questionId").notNull(),
  documentType: mysqlEnum("documentType", ["exam_sheet", "presentation_slides"]).notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  documentUrl: text("documentUrl").notNull(),
  documentKey: text("documentKey").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type GeneratedDocument = typeof generatedDocuments.$inferSelect;
export type InsertGeneratedDocument = typeof generatedDocuments.$inferInsert;


/**
 * Learning Projects - Student-created learning contexts
 */
export const learningProjects = mysqlTable("learningProjects", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  title: text("title").notNull(),
  description: text("description"),
  initialContext: text("initialContext"), // Initial context provided by student
  objectives: text("objectives"), // Learning objectives (JSON array)
  color: varchar("color", { length: 7 }).default("#0EA5E9"), // Hex color for UI
  isActive: boolean("isActive").default(true).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type LearningProject = typeof learningProjects.$inferSelect;
export type InsertLearningProject = typeof learningProjects.$inferInsert;

/**
 * Project Context - Track learning progress and context within a project
 */
export const projectContexts = mysqlTable("projectContexts", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("projectId").notNull(),
  userId: int("userId").notNull(),
  contextData: text("contextData"), // JSON object storing accumulated knowledge
  lastUpdated: timestamp("lastUpdated").defaultNow().onUpdateNow().notNull(),
});

export type ProjectContext = typeof projectContexts.$inferSelect;
export type InsertProjectContext = typeof projectContexts.$inferInsert;

/**
 * Project Questions - Link questions to learning projects
 */
export const projectQuestions = mysqlTable("projectQuestions", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("projectId").notNull(),
  questionId: int("questionId").notNull(),
  addedAt: timestamp("addedAt").defaultNow().notNull(),
});

export type ProjectQuestion = typeof projectQuestions.$inferSelect;
export type InsertProjectQuestion = typeof projectQuestions.$inferInsert;
