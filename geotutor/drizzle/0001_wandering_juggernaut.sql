CREATE TABLE `answers` (
	`id` int AUTO_INCREMENT NOT NULL,
	`questionId` int NOT NULL,
	`answerText` text NOT NULL,
	`visualUrl` text,
	`visualKey` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `answers_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `assignmentSubmissions` (
	`id` int AUTO_INCREMENT NOT NULL,
	`assignmentId` int NOT NULL,
	`studentId` int NOT NULL,
	`completed` boolean NOT NULL DEFAULT false,
	`submittedAt` timestamp,
	CONSTRAINT `assignmentSubmissions_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `assignments` (
	`id` int AUTO_INCREMENT NOT NULL,
	`classroomId` int NOT NULL,
	`title` varchar(255) NOT NULL,
	`description` text,
	`assignmentType` enum('question','module') NOT NULL,
	`referenceId` int,
	`dueDate` timestamp,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `assignments_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `classroomStudents` (
	`id` int AUTO_INCREMENT NOT NULL,
	`classroomId` int NOT NULL,
	`studentId` int NOT NULL,
	`enrolledAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `classroomStudents_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `classrooms` (
	`id` int AUTO_INCREMENT NOT NULL,
	`teacherId` int NOT NULL,
	`name` varchar(255) NOT NULL,
	`description` text,
	`inviteCode` varchar(32) NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `classrooms_id` PRIMARY KEY(`id`),
	CONSTRAINT `classrooms_inviteCode_unique` UNIQUE(`inviteCode`)
);
--> statement-breakpoint
CREATE TABLE `moduleProgress` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`moduleId` int NOT NULL,
	`completed` boolean NOT NULL DEFAULT false,
	`progressPercent` int NOT NULL DEFAULT 0,
	`lastAccessedAt` timestamp NOT NULL DEFAULT (now()),
	`completedAt` timestamp,
	CONSTRAINT `moduleProgress_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `modules` (
	`id` int AUTO_INCREMENT NOT NULL,
	`title` varchar(255) NOT NULL,
	`description` text NOT NULL,
	`content` text NOT NULL,
	`difficulty` enum('beginner','intermediate','advanced') NOT NULL,
	`estimatedMinutes` int NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `modules_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `questions` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`questionText` text NOT NULL,
	`includeVisual` boolean NOT NULL DEFAULT false,
	`visualType` enum('flowchart','diagram','infographic','illustration'),
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `questions_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `savedContent` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`questionId` int NOT NULL,
	`tags` text,
	`notes` text,
	`savedAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `savedContent_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `workspaceParticipants` (
	`id` int AUTO_INCREMENT NOT NULL,
	`workspaceId` int NOT NULL,
	`userId` int NOT NULL,
	`role` enum('owner','editor','viewer') NOT NULL DEFAULT 'editor',
	`joinedAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `workspaceParticipants_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `workspaces` (
	`id` int AUTO_INCREMENT NOT NULL,
	`name` varchar(255) NOT NULL,
	`createdBy` int NOT NULL,
	`content` text NOT NULL,
	`classroomId` int,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `workspaces_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
ALTER TABLE `users` MODIFY COLUMN `role` enum('user','admin','teacher','student') NOT NULL DEFAULT 'student';