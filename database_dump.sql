-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: pos_qr_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `floor_layouts`
--

DROP TABLE IF EXISTS `floor_layouts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `floor_layouts` (
  `tenant_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `floor` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `grid_cols` int NOT NULL DEFAULT '12',
  `grid_row_px` int NOT NULL DEFAULT '90',
  `grid_gap_px` int NOT NULL DEFAULT '6',
  `boxes` json NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `updated_by_user_id` int DEFAULT NULL,
  PRIMARY KEY (`tenant_id`,`floor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `floor_layouts`
--

LOCK TABLES `floor_layouts` WRITE;
/*!40000 ALTER TABLE `floor_layouts` DISABLE KEYS */;
/*!40000 ALTER TABLE `floor_layouts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_items`
--

DROP TABLE IF EXISTS `order_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `order_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tenant_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `table_number` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `qty` decimal(10,1) NOT NULL,
  `price` int NOT NULL,
  `total_price` int NOT NULL,
  `sauce` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `note` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'new',
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by_user_id` int DEFAULT NULL,
  `updated_by_user_id` int DEFAULT NULL,
  `bill_group` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `void_qty` decimal(10,1) NOT NULL DEFAULT '0.0',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_order_items_tenant` (`tenant_id`),
  KEY `idx_order_items_session` (`tenant_id`,`session_id`,`bill_group`),
  KEY `idx_order_items_status` (`tenant_id`,`status`),
  KEY `idx_order_items_ts` (`tenant_id`,`timestamp`),
  KEY `fk_order_items_session` (`session_id`),
  CONSTRAINT `fk_order_items_session` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_items`
--

LOCK TABLES `order_items` WRITE;
/*!40000 ALTER TABLE `order_items` DISABLE KEYS */;
INSERT INTO `order_items` VALUES (5,'default','5bc44691-10f6-40e9-96d4-901bf8cb8f90','5','Sweets',2.0,100,200,NULL,'Extra chocolate','new','2026-11-17 18:49:03',1,NULL,'main',0.0,'2026-11-17 18:49:03'),(6,'default','99f1c83c-dc8b-4cf3-985b-960838968888','5','Sweets',2.0,0,0,NULL,'Extra chocolate','new','2026-11-17 18:49:45',1,NULL,'main',0.0,'2026-11-17 18:49:45'),(7,'default','bb24f3cf-4dc3-482b-986d-e4768c14364c','5','Sweets',2.0,0,0,NULL,'Extra chocolate','new','2026-11-17 18:51:39',1,NULL,'main',0.0,'2026-11-17 18:51:39');
/*!40000 ALTER TABLE `order_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments`
--

DROP TABLE IF EXISTS `payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tenant_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `amount` int NOT NULL DEFAULT '0',
  `method` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `paid_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `cash_received` int DEFAULT NULL,
  `change_given` int DEFAULT NULL,
  `discount_percent` int DEFAULT '0',
  `discount_amount` int DEFAULT '0',
  `tax` int DEFAULT '0',
  `service` int DEFAULT '0',
  `total_before_discount` int DEFAULT '0',
  `card_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `bill_group` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dp_applied_amount` int DEFAULT '0',
  `is_refund` tinyint(1) NOT NULL DEFAULT '0',
  `refund_of` int DEFAULT NULL,
  `refund_reason` text COLLATE utf8mb4_unicode_ci,
  `refunded_by_user_id` int DEFAULT NULL,
  `is_dp` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_payments_tenant` (`tenant_id`),
  KEY `idx_payments_session` (`tenant_id`,`session_id`),
  KEY `idx_payments_paid_at` (`tenant_id`,`paid_at`),
  KEY `idx_payments_is_refund` (`tenant_id`,`is_refund`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments`
--

LOCK TABLES `payments` WRITE;
/*!40000 ALTER TABLE `payments` DISABLE KEYS */;
/*!40000 ALTER TABLE `payments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `qr_orders`
--

DROP TABLE IF EXISTS `qr_orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qr_orders` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tenant_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `table_number` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `guest_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `items` json NOT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'new',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `sent_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_qr_tenant` (`tenant_id`),
  KEY `idx_qr_table` (`tenant_id`,`table_number`,`status`),
  KEY `idx_qr_status` (`tenant_id`,`status`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `qr_orders`
--

LOCK TABLES `qr_orders` WRITE;
/*!40000 ALTER TABLE `qr_orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `qr_orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reservation_items`
--

DROP TABLE IF EXISTS `reservation_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reservation_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tenant_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `reservation_id` int NOT NULL,
  `item_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `qty` int NOT NULL DEFAULT '1',
  `price` int NOT NULL DEFAULT '0',
  `sauce` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by_user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_res_items_tenant` (`tenant_id`),
  KEY `idx_res_items_res` (`tenant_id`,`reservation_id`),
  KEY `fk_res_items_res` (`reservation_id`),
  CONSTRAINT `fk_res_items_res` FOREIGN KEY (`reservation_id`) REFERENCES `reservations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reservation_items`
--

LOCK TABLES `reservation_items` WRITE;
/*!40000 ALTER TABLE `reservation_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `reservation_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reservations`
--

DROP TABLE IF EXISTS `reservations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reservations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tenant_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `guest_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `pax` int NOT NULL DEFAULT '1',
  `date` date NOT NULL,
  `time` time NOT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `table_number` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `session_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by_user_id` int DEFAULT NULL,
  `confirmed_by_user_id` int DEFAULT NULL,
  `seated_by_user_id` int DEFAULT NULL,
  `dp_amount` int NOT NULL DEFAULT '0',
  `dp_method` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dp_paid_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_res_tenant` (`tenant_id`),
  KEY `idx_res_date_time` (`tenant_id`,`date`,`time`),
  KEY `idx_res_status` (`tenant_id`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reservations`
--

LOCK TABLES `reservations` WRITE;
/*!40000 ALTER TABLE `reservations` DISABLE KEYS */;
/*!40000 ALTER TABLE `reservations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sessions`
--

DROP TABLE IF EXISTS `sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sessions` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tenant_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `pax` int DEFAULT '1',
  `table_number` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `guest_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dp_amount` int DEFAULT '0',
  `dp_method` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dp_paid_at` datetime DEFAULT NULL,
  `note` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT 'active',
  `closed_at` datetime DEFAULT NULL,
  `opened_by_user_id` int DEFAULT NULL,
  `closed_by_user_id` int DEFAULT NULL,
  `split_labels` text COLLATE utf8mb4_unicode_ci,
  `split_meta` json DEFAULT NULL,
  `lock_user_id` int DEFAULT NULL,
  `lock_until` datetime DEFAULT NULL,
  `lock_nonce` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `lock_acquired_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `billing_started_at` datetime DEFAULT NULL,
  `service_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'dine_in',
  `pickup_time` datetime DEFAULT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `reopened_at` datetime DEFAULT NULL,
  `reopened_by_user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_sessions_tenant` (`tenant_id`),
  KEY `idx_sessions_table` (`tenant_id`,`table_number`,`status`),
  KEY `idx_sessions_status` (`tenant_id`,`status`),
  KEY `idx_sessions_created` (`tenant_id`,`created_at`),
  KEY `idx_sessions_closed` (`tenant_id`,`closed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sessions`
--

LOCK TABLES `sessions` WRITE;
/*!40000 ALTER TABLE `sessions` DISABLE KEYS */;
INSERT INTO `sessions` VALUES ('01c6c298-f499-41b7-8045-3cd607ebd265','default',2,'5','2026-11-17 18:41:06','David',0,NULL,NULL,NULL,'active',NULL,1,NULL,NULL,NULL,1,'2026-11-17 18:42:36','21913497-9e8f-48f0-94d5-c6518db6e197','2026-11-17 18:41:05',NULL,'dine_in',NULL,'2026-11-17 18:41:05',NULL,NULL),('5bc44691-10f6-40e9-96d4-901bf8cb8f90','default',2,'5','2026-11-17 18:44:39','David',0,NULL,NULL,NULL,'active',NULL,1,NULL,NULL,NULL,1,'2026-11-17 18:46:09','753b931c-90e2-47ca-bba3-02bd12a5e16a','2026-11-17 18:44:38',NULL,'dine_in',NULL,'2026-11-17 18:44:38',NULL,NULL),('99f1c83c-dc8b-4cf3-985b-960838968888','default',2,'5','2026-11-17 18:49:45','David',0,NULL,NULL,NULL,'active',NULL,1,NULL,NULL,NULL,1,'2026-11-17 18:51:15','05601ff4-c2ac-4c52-9cf0-95507b4e25e7','2026-11-17 18:49:44',NULL,'dine_in',NULL,'2026-11-17 18:49:44',NULL,NULL),('bb24f3cf-4dc3-482b-986d-e4768c14364c','default',2,'5','2026-11-17 18:51:39','David',0,NULL,NULL,NULL,'active',NULL,1,NULL,NULL,NULL,1,'2026-11-17 18:53:10','eeef3838-e0f4-486a-b281-ebc58af86ffb','2026-11-17 18:51:39',NULL,'dine_in',NULL,'2026-11-17 18:51:39',NULL,NULL),('f7b442f7-3a4b-451d-927e-933d7d625bf8','default',2,'5','2026-11-17 18:43:09','David',0,NULL,NULL,NULL,'active',NULL,1,NULL,NULL,NULL,1,'2026-11-17 18:44:39','6d034165-72d8-44ef-9d37-6a26c7ce1969','2026-11-17 18:43:08',NULL,'dine_in',NULL,'2026-11-17 18:43:08',NULL,NULL);
/*!40000 ALTER TABLE `sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tenant_feedback`
--

DROP TABLE IF EXISTS `tenant_feedback`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tenant_feedback` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tenant_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `table_number` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `session_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `customer_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rating` int NOT NULL DEFAULT '5',
  `food_rating` int DEFAULT '5',
  `service_rating` int DEFAULT '5',
  `comments` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_feedback_tenant` (`tenant_id`),
  KEY `idx_feedback_created` (`tenant_id`,`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tenant_feedback`
--

LOCK TABLES `tenant_feedback` WRITE;
/*!40000 ALTER TABLE `tenant_feedback` DISABLE KEYS */;
INSERT INTO `tenant_feedback` VALUES (1,'default','T1','test-session-123','Alice Smith',5,5,4,'Super tasty fish and fast service!','2026-11-17 18:38:17'),(2,'default','5','bb24f3cf-4dc3-482b-986d-e4768c14364c','David',5,5,5,'Loved the quick QR ordering and great sweets!','2026-11-17 18:51:39');
/*!40000 ALTER TABLE `tenant_feedback` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tenants`
--

DROP TABLE IF EXISTS `tenants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tenants` (
  `id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT 'Restaurant POS',
  `currency_symbol` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT '$',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tenants`
--

LOCK TABLES `tenants` WRITE;
/*!40000 ALTER TABLE `tenants` DISABLE KEYS */;
INSERT INTO `tenants` VALUES ('branch2','Downtown Bistro','Downtown Gourmet & Bistro','$',1,'2026-11-17 17:45:26'),('default','Main Branch Restaurant','OpenPOS & QR Gourmet','$',1,'2026-11-17 17:45:26');
/*!40000 ALTER TABLE `tenants` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tenant_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `username` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `full_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `demo_password_plain` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'cashier',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_tenant_username` (`tenant_id`,`username`),
  KEY `idx_users_tenant` (`tenant_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'default','admin','System Administrator','$2b$10$tWM0VV943NaxEIGR63U9OuBNsBN9ID8rjkJxfznETUoMEFHmAPo5O','admin123','admin',1,'2026-11-17 17:45:26'),(2,'default','cashier','Main Cashier','$2b$10$3JNUFSmpGoQqJO.tpY80VuajqtoKH4nPw.AcvGvl592NE7YFsEp6i','cashier123','cashier',1,'2026-11-17 17:45:26'),(3,'default','waiter','Front Waiter','$2b$10$xeNYAAjkiZQ5awH7zTGXde3/KVRI0rlaAz8lQw3C830wDtRzM2svK','waiter123','waiter',1,'2026-11-17 17:45:26'),(4,'branch2','admin','Downtown Admin','$2b$10$tWM0VV943NaxEIGR63U9OuBNsBN9ID8rjkJxfznETUoMEFHmAPo5O','admin123','admin',1,'2026-11-17 17:45:26');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-17 21:48:51
