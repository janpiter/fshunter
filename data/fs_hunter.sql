-- phpMyAdmin SQL Dump
-- version 4.7.7
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Aug 05, 2018 at 07:41 AM
-- Server version: 5.7.20
-- PHP Version: 7.1.16

SET FOREIGN_KEY_CHECKS=0;
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `fs_hunter`
--
CREATE DATABASE IF NOT EXISTS `fs_hunter` DEFAULT CHARACTER SET latin1 COLLATE latin1_swedish_ci;
USE `fs_hunter`;

-- --------------------------------------------------------

--
-- Table structure for table `fs_items`
--

CREATE TABLE IF NOT EXISTS `fs_items` (
  `item_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `mp_id` int(11) NOT NULL,
  `item_name` varchar(255) NOT NULL,
  `item_link` varchar(500) NOT NULL,
  `item_picture` varchar(500) DEFAULT NULL,
  `item_discount` int(11) NOT NULL DEFAULT '0',
  `item_price_after` bigint(20) NOT NULL DEFAULT '0',
  `item_price_before` bigint(20) NOT NULL DEFAULT '0',
  `item_start_date` datetime NOT NULL,
  `item_end_date` datetime NOT NULL,
  `item_status` enum('0','1') NOT NULL COMMENT '0:expired; 1:active',
  PRIMARY KEY (`item_id`),
  KEY `mp_id` (`mp_id`),
  KEY `item_link` (`item_link`),
  KEY `item_discount` (`item_discount`),
  KEY `item_status` (`item_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `fs_marketplace`
--

CREATE TABLE IF NOT EXISTS `fs_marketplace` (
  `mp_id` int(11) NOT NULL AUTO_INCREMENT,
  `mp_name` varchar(100) NOT NULL,
  `mp_link` varchar(255) NOT NULL,
  `mp_sessions_link` varchar(255) NOT NULL COMMENT 'flash sale index page',
  `mp_items_link` varchar(255) NOT NULL,
  `mp_status` enum('0','1') NOT NULL DEFAULT '1' COMMENT '0: incative; 1:active',
  `mp_created_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`mp_id`),
  UNIQUE KEY `mp_link` (`mp_link`),
  KEY `mp_sessions_link` (`mp_sessions_link`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `fs_marketplace`
--

INSERT DELAYED IGNORE INTO `fs_marketplace` (`mp_id`, `mp_name`, `mp_link`, `mp_sessions_link`, `mp_items_link`, `mp_status`, `mp_created_date`) VALUES
(1, 'Shopee', 'https://shopee.co.id', 'https://shopee.co.id/api/v2/flash_sale/get_all_sessions', 'https://shopee.co.id/api/v2/flash_sale/get_items?offset={offset}&limit={limit}&promotionid={promotionid}', '1', '2018-08-05 06:51:58');

-- --------------------------------------------------------

--
-- Table structure for table `fs_rules`
--

CREATE TABLE IF NOT EXISTS `fs_rules` (
  `rule_id` int(11) NOT NULL AUTO_INCREMENT,
  `mp_id` int(11) NOT NULL,
  `rule_type` enum('json','css') NOT NULL,
  `rule_sessions_list` varchar(100) NOT NULL COMMENT 'rule for get properties in sessions page',
  `rule_items_list` varchar(100) NOT NULL COMMENT 'rule for get items in items page',
  `rule_item_name` varchar(100) NOT NULL,
  `rule_item_link` varchar(100) NOT NULL,
  `rule_item_picture` varchar(100) NOT NULL,
  `rule_item_discount` varchar(100) NOT NULL,
  `rule_item_price_before` varchar(100) NOT NULL,
  `rule_item_price_after` varchar(100) NOT NULL,
  `rule_item_start_time` varchar(100) NOT NULL,
  `rule_item_end_time` varchar(100) NOT NULL,
  PRIMARY KEY (`rule_id`),
  UNIQUE KEY `mp_id` (`mp_id`),
  KEY `rule_item_link` (`rule_item_link`),
  KEY `rule_item_name` (`rule_item_name`),
  KEY `rule_item_discount` (`rule_item_discount`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `fs_rules`
--

INSERT DELAYED IGNORE INTO `fs_rules` (`rule_id`, `mp_id`, `rule_type`, `rule_sessions_list`, `rule_items_list`, `rule_item_name`, `rule_item_link`, `rule_item_picture`, `rule_item_discount`, `rule_item_price_before`, `rule_item_price_after`, `rule_item_start_time`, `rule_item_end_time`) VALUES
(1, 1, 'json', 'data|sessions[]|promotionid', 'data|items[]', 'name', 'shopid,itemid', 'promo_images[]', 'raw_discount', 'price_before_discount', 'price', 'start_time', 'end_time');
SET FOREIGN_KEY_CHECKS=1;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
