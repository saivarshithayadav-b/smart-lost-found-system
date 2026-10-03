-- MySQL dump 10.13  Distrib 26.7.0, for macos26.6 (arm64)
--
-- Host: localhost    Database: lost_found_db
-- ------------------------------------------------------
-- Server version	26.7.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '2e651a3e-b75a-11f1-9ad2-df356c7b2750:1-14';


--
-- Table structure for table `found_items`
--

DROP TABLE IF EXISTS `found_items`;

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;

CREATE TABLE `found_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `item_name` varchar(100) NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `description` text,
  `color` varchar(50) DEFAULT NULL,
  `brand` varchar(100) DEFAULT NULL,
  `found_date` date DEFAULT NULL,
  `location` varchar(255) DEFAULT NULL,
  `latitude` decimal(10,8) DEFAULT NULL,
  `longitude` decimal(11,8) DEFAULT NULL,
  `image_path` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `found_items_ibfk_1`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`id`)
) ENGINE=InnoDB
  AUTO_INCREMENT=3
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Dumping data for table `found_items`
--

LOCK TABLES `found_items` WRITE;

/*!40000 ALTER TABLE `found_items` DISABLE KEYS */;

INSERT INTO `found_items`
VALUES
(
  1,
  2,
  'Black Wallet',
  'Wallet',
  'Black leather wallet',
  'Black',
  'Puma',
  '2026-09-23',
  'college campus',
  NULL,
  NULL,
  NULL,
  '2026-09-23 16:32:55'
),
(
  2,
  2,
  'Blue Bag',
  'Bag',
  '',
  'Blue',
  'Skybags',
  '2026-09-24',
  'college campus',
  NULL,
  NULL,
  'Screenshot_2026-09-24_at_7.02.55_PM.png',
  '2026-09-24 13:35:27'
);

/*!40000 ALTER TABLE `found_items` ENABLE KEYS */;

UNLOCK TABLES;


--
-- Table structure for table `lost_items`
--

DROP TABLE IF EXISTS `lost_items`;

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;

CREATE TABLE `lost_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `item_name` varchar(100) NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `description` text,
  `color` varchar(50) DEFAULT NULL,
  `brand` varchar(100) DEFAULT NULL,
  `lost_date` date DEFAULT NULL,
  `location` varchar(255) DEFAULT NULL,
  `latitude` decimal(10,8) DEFAULT NULL,
  `longitude` decimal(11,8) DEFAULT NULL,
  `image_path` varchar(255) DEFAULT NULL,

  -- Private ownership verification details
  `verification_0` text,
  `verification_1` text,
  `verification_2` text,
  `verification_3` text,

  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),

  CONSTRAINT `lost_items_ibfk_1`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`id`)
) ENGINE=InnoDB
  AUTO_INCREMENT=7
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Dumping data for table `lost_items`
--

LOCK TABLES `lost_items` WRITE;

/*!40000 ALTER TABLE `lost_items` DISABLE KEYS */;

INSERT INTO `lost_items`
(
  id,
  user_id,
  item_name,
  category,
  description,
  color,
  brand,
  lost_date,
  location,
  latitude,
  longitude,
  image_path,
  verification_0,
  verification_1,
  verification_2,
  verification_3,
  created_at
)
VALUES
(
  1,
  2,
  'Black Wallet',
  'Wallet',
  'Black leather wallet',
  'Black',
  'Puma',
  '2026-09-23',
  'college campus',
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  '2026-09-23 16:08:40'
),
(
  2,
  2,
  'Black Wallet',
  'Wallet',
  'Black leather wallet',
  'Black',
  'Puma',
  '2026-09-24',
  'college campus',
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  '2026-09-24 10:27:31'
),
(
  3,
  2,
  'Black Wallet',
  'Wallet',
  'Black Leather Wallet',
  'Black',
  'Puma',
  '2026-09-24',
  'college campus',
  NULL,
  NULL,
  'uploads/Screenshot_2026-09-24_at_6.47.38_PM.png',
  NULL,
  NULL,
  NULL,
  NULL,
  '2026-09-24 13:18:29'
),
(
  4,
  2,
  'Blue Bag',
  'Bag',
  'Blue college bag',
  'Blue',
  'Skybags',
  '2026-09-24',
  'college campus',
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  '2026-09-24 13:26:54'
),
(
  5,
  2,
  'Blue Bag',
  'Bag',
  'Blue college bag',
  'Blue',
  'Skybags',
  '2026-09-24',
  'college campus',
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  '2026-09-24 13:27:11'
),
(
  6,
  2,
  'Blue Bag',
  'Bag',
  'Blue college bag',
  'Blue',
  'Skybags',
  '2026-09-24',
  'college campus',
  NULL,
  NULL,
  'Screenshot_2026-09-24_at_7.02.55_PM.png',
  NULL,
  NULL,
  NULL,
  NULL,
  '2026-09-24 13:33:11'
);

/*!40000 ALTER TABLE `lost_items` ENABLE KEYS */;

UNLOCK TABLES;


--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB
  AUTO_INCREMENT=3
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;

/*!40000 ALTER TABLE `users` DISABLE KEYS */;

INSERT INTO `users`
VALUES
(
  1,
  'varshitha',
  'saivarshithayadav@gmail.com',
  'REPLACE_WITH_A_HASHED_PASSWORD',
  '2026-09-23 15:29:26'
),
(
  2,
  'varsh',
  'ponky@gmail.com',
  'scrypt:32768:8:1$lmjcHOqC3OV9QTKH$76c53aba317accb6ecd57bae76273a2c85f488e29acd7dda214776338c1acf15e17576f38ab4167b4a8a9954ee725b73aad0e6e16b7caef74108014e6e2b772c',
  '2026-09-23 15:33:52'
);

/*!40000 ALTER TABLE `users` ENABLE KEYS */;

UNLOCK TABLES;


SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;