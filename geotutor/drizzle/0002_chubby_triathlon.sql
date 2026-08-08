CREATE TABLE `generatedDocuments` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`questionId` int NOT NULL,
	`documentType` enum('exam_sheet','presentation_slides') NOT NULL,
	`title` varchar(255) NOT NULL,
	`documentUrl` text NOT NULL,
	`documentKey` text NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `generatedDocuments_id` PRIMARY KEY(`id`)
);
