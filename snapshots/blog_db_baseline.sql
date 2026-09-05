-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: blog_db
-- ------------------------------------------------------
-- Server version	8.0.44

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
-- Table structure for table `article`
--

DROP TABLE IF EXISTS `article`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `article` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `content` text NOT NULL,
  `summary` varchar(500) DEFAULT NULL,
  `author_id` bigint NOT NULL,
  `category_id` bigint DEFAULT NULL,
  `status` tinyint NOT NULL DEFAULT '1' COMMENT '1-已发布 0-草稿',
  `view_count` int NOT NULL DEFAULT '0',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted` tinyint NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_author_id` (`author_id`),
  KEY `idx_category_id` (`category_id`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=488 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `article`
--

LOCK TABLES `article` WRITE;
/*!40000 ALTER TABLE `article` DISABLE KEYS */;
INSERT INTO `article` VALUES (1,'Spring Boot 入门指南','# Spring Boot 入门指南\n\n## 什么是 Spring Boot？\n\nSpring Boot 是 Spring 框架的扩展，它简化了 Spring 应用的创建和开发过程。\n\n## 核心特性\n\n- **自动配置**：根据添加的依赖自动配置 Spring 应用\n- **起步依赖**：简化 Maven/Gradle 配置\n- **内嵌服务器**：内置 Tomcat、Jetty 等\n\n## 快速开始\n\n```java\n@SpringBootApplication\npublic class MyApp {\n    public static void main(String[] args) {\n        SpringApplication.run(MyApp.class, args);\n    }\n}\n```\n\n> Spring Boot 让 Java 开发变得更加简单和高效！','Spring Boot 入门指南 什么是 Spring Boot？ Spring Boot 是 Spring 框架的扩展，它简化了 Spring 应用的创建和开发过程。 核心特性 自动配置 ：根据添加的依赖自动配置 Spring 应用 起步依赖 ：简化 Maven/Gradle 配置 内嵌服务器 ：...',1,1,1,223,'2026-05-28 17:04:56','2026-08-28 18:58:22',0),(2,'Vue 3 组合式 API 详解','# Vue 3 组合式 API 详解\n\n## 为什么需要组合式 API？\n\nVue 3 引入了组合式 API，提供更灵活的组件逻辑组织方式。\n\n## 核心概念\n\n```javascript\nimport { ref, reactive } from \'vue\'\n\nconst count = ref(0)\nconst state = reactive({ name: \'Vue\', version: 3 })\n```\n\n## 优势\n- 更好的逻辑复用\n- 更灵活的代码组织\n- 更好的类型推导','Vue 3 组合式 API 详解 为什么需要组合式 API？ Vue 3 引入了组合式 API，提供更灵活的组件逻辑组织方式。 核心概念 javascript import { ref, reactive } from \'vue\' const count = ref 0 const state = ...',1,1,1,99,'2026-05-28 17:04:56','2026-08-28 17:18:29',1),(3,'我的 2024 年终总结','# 2024 年终总结\n\n时光飞逝，转眼间 2024 年即将过去。\n\n## 技术成长\n\n- 深入学习了 Spring Boot 和微服务架构\n- 掌握了 Vue 3 和 TypeScript\n- 参与了两个大型项目的开发\n\n## 生活感悟\n\n- 坚持每周运动 3 次\n- 读完了 12 本书\n- 去了 3 个城市旅行\n\n> 不断学习，保持好奇心，享受生活。','2024 年终总结 时光飞逝，转眼间 2024 年即将过去。 技术成长 深入学习了 Spring Boot 和微服务架构 掌握了 Vue 3 和 TypeScript 参与了两个大型项目的开发 生活感悟 坚持每周运动 3 次 读完了 12 本书 去了 3 个城市旅行 不断学习，保持好奇心，享受生活。',2,2,1,225,'2026-05-28 17:04:56','2026-08-28 18:58:22',0),(4,'MySQL 索引优化实战','# MySQL 索引优化实战\n\n## 索引的重要性\n\n正确的索引可以让查询速度提升百倍。\n\n## 联合索引\n\n```sql\nCREATE INDEX idx_name_age ON user(name, age);\n```\n\n**最左前缀原则**：查询条件必须从索引最左列开始。\n\n## 实战案例\n\n```sql\nEXPLAIN SELECT * FROM orders WHERE user_id = 100 AND status = 1;\n```\n\n优化后执行时间从 2.3 秒降到 0.01 秒。','MySQL 索引优化实战 索引的重要性 正确的索引可以让查询速度提升百倍。 联合索引 sql CREATE INDEX idx_name_age ON user name, age ; 最左前缀原则 ：查询条件必须从索引最左列开始。 实战案例 sql EXPLAIN SELECT FROM orde...',2,1,1,164,'2026-05-28 17:04:56','2026-08-28 16:06:05',0),(5,'JavaScript 异步编程完全指南','# JavaScript 异步编程完全指南\n\n## 异步编程的发展\n\n1. **回调函数** → 回调地狱\n2. **Promise** → 链式调用\n3. **async/await** → 同步写法\n\n```javascript\nasync function getData() {\n  try {\n    const data = await fetchData()\n    console.log(data)\n  } catch (error) {\n    console.error(error)\n  }\n}\n```','JavaScript 异步编程完全指南 异步编程的发展 1. 回调函数 → 回调地狱 2. Promise → 链式调用 3. async/await → 同步写法 javascript async function getData { try { const data = await fetchD...',3,1,1,94,'2026-05-28 17:04:56','2026-08-26 22:56:04',0),(6,'CSS 现代布局技巧','# CSS 现代布局技巧\n\n## Flexbox\n\n```css\n.container {\n  display: flex;\n  justify-content: center;\n  align-items: center;\n}\n```\n\n## Grid\n\n```css\n.grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));\n  gap: 20px;\n}\n```\n\n> 现代 CSS 让布局变得简单而强大！','CSS 现代布局技巧 Flexbox css .container { display: flex; justify content: center; align items: center; } Grid css .grid { display: grid; grid template colum...',3,1,1,80,'2026-05-28 17:04:56','2026-08-26 16:03:22',0),(7,'Python 数据分析入门','# Python 数据分析入门\n\n## 核心库\n\n### Pandas\n\n```python\nimport pandas as pd\ndf = pd.read_csv(\'data.csv\')\nprint(df.describe())\n```\n\n### NumPy\n\n```python\nimport numpy as np\narr = np.array([1, 2, 3, 4, 5])\nprint(np.mean(arr))\n```\n\n> Python 让数据分析变得触手可及！','Python 数据分析入门 核心库 Pandas python import pandas as pd df = pd.read_csv \'data.csv\' print df.describe NumPy python import numpy as np arr = np.array 1, 2,...',1,1,1,141,'2026-05-28 17:04:56','2026-08-27 19:36:31',0),(8,'程序员的周末时光','# 程序员的周末时光\n\n## 周六\n\n睡到自然醒，泡一杯咖啡。上午学习新技术，下午户外运动。\n\n## 周日\n\n上午整理房间做做饭，下午写写博客，晚上准备新一周的工作。\n\n> 工作是为了更好地生活，别忘了享受当下！','程序员的周末时光 周六 睡到自然醒，泡一杯咖啡。上午学习新技术，下午户外运动。 周日 上午整理房间做做饭，下午写写博客，晚上准备新一周的工作。 工作是为了更好地生活，别忘了享受当下！',2,2,1,68,'2026-05-28 17:04:56','2026-08-27 19:45:38',0),(9,'如何写出高质量的代码','# 如何写出高质量的代码\n\n## 命名规范\n\n```java\n// Bad\nint d;\n// Good\nint daysSinceCreation;\n```\n\n## 函数设计\n- 一个函数只做一件事\n- 函数体不超过 20 行\n\n## 推荐书籍\n1.《代码整洁之道》\n2.《重构》\n3.《设计模式》\n\n> 写代码是一门手艺，需要不断打磨！','如何写出高质量的代码 命名规范 java // Bad int d; // Good int daysSinceCreation; 函数设计 一个函数只做一件事 函数体不超过 20 行 推荐书籍 1.《代码整洁之道》 2.《重构》 3.《设计模式》 写代码是一门手艺，需要不断打磨！',1,3,1,193,'2026-05-28 17:04:56','2026-08-26 17:14:32',0),(10,'HTML5 新特性速览','# HTML5 新特性速览\n\n## 语义化标签\n\n```html\n<header>页头</header>\n<nav>导航</nav>\n<main>主体</main>\n<article>文章</article>\n```\n\n## 本地存储\n\n```javascript\nlocalStorage.setItem(\'key\', \'value\')\n```\n\n> HTML5 让 Web 开发更加强大！','HTML5 新特性速览 语义化标签 html <header 页头</header <nav 导航</nav <main 主体</main <article 文章</article 本地存储 javascript localStorage.setItem \'key\', \'value\' HTML5 让...',3,4,1,108,'2026-05-28 17:04:56','2026-08-30 23:40:43',0),(11,'Docker 入门1','# Docker 入门\n\n正在编写中...\n\n## TODO\n- 容器概念\n- Dockerfile\n- Docker Compose','Docker 入门 正在编写中... TODO 容器概念 Dockerfile Docker Compose',2,1,0,6,'2026-05-28 17:04:56','2026-08-25 22:12:33',1),(12,'test1','2','1',2,3,1,56,'2026-05-31 14:37:44','2026-08-25 11:26:23',1),(13,'API Test Article','This is a test article via API','This is a test article via API',2,1,1,0,'2026-06-01 18:30:16','2026-06-01 18:32:31',1),(14,'Browser Test Article','Testing publish from browser','',2,NULL,1,0,'2026-06-01 18:31:32','2026-06-01 18:32:19',1),(15,'test2','123\n\n4\n\n5\n\n\n\n\n\n\n\n\n\n\n1','1',2,3,1,33,'2026-06-03 20:03:58','2026-08-27 21:42:56',0),(16,'我的第一篇文章','# Hello\n\n这是正文内容...','这是摘要',1,1,1,0,'2026-07-06 22:10:17','2026-08-25 14:48:09',1),(481,'asyncio 的基本用法','1. 运行协程\n要运行一个协程，你可以使用 asyncio.run() 函数。它会创建一个事件循环，并运行指定的协程。\n\n实例\n```\nimport asyncio\n\nasync def main():\n    print(\"Start\")\n    await asyncio.sleep(1)\n    print(\"End\")\n\nasyncio.run(main())\n```\n2. 并发执行多个任务\n你可以使用 asyncio.gather() 函数并发执行多个协程，并等待它们全部完成。\n\n实例\n```\nimport asyncio\n\nasync def task1():\n    print(\"Task 1 started\")\n    await asyncio.sleep(1)\n    print(\"Task 1 finished\")\n\nasync def task2():\n    print(\"Task 2 started\")\n    await asyncio.sleep(2)\n    print(\"Task 2 finished\")\n\nasync def main():\n    await asyncio.gather(task1(), task2())\n\nasyncio.run(main())\n```\n3. 超时控制\n你可以使用 asyncio.wait_for() 函数为协程设置超时时间。如果协程在指定时间内未完成，将引发 asyncio.TimeoutError 异常。\n\n实例\n```\nimport asyncio\n\nasync def long_task():\n    await asyncio.sleep(10)\n    print(\"Task finished\")\n\nasync def main():\n    try:\n        await asyncio.wait_for(long_task(), timeout=5)\n    except asyncio.TimeoutError:\n        print(\"Task timed out\")\n\nasyncio.run(main())\n```','1. 运行协程 要运行一个协程，你可以使用 asyncio.run 函数。它会创建一个事件循环，并运行指定的协程。 实例 import asyncio async def main : print \"Start\" await asyncio.sleep 1 print \"End\" asyncio.r',2,1,1,2,'2026-08-27 18:20:38','2026-08-27 18:20:50',0),(482,'asyncio 的应用场景','网络请求：如 HTTP 请求、WebSocket 通信等。\n文件 I/O：如异步读写文件。\n数据库操作：如异步访问数据库。\n实时数据处理：如实时消息队列处理。','网络请求：如 HTTP 请求、WebSocket 通信等。 文件 I/O：如异步读写文件。 数据库操作：如异步访问数据库。 实时数据处理：如实时消息队列处理。',2,3,1,0,'2026-08-27 18:22:00','2026-08-27 18:22:00',0),(483,'asyncio注意事项','注意事项\nPython版本：部分功能需Python 3.7+（如asyncio.run()）。\n\n阻塞操作：避免在协程中使用同步阻塞代码（如time.sleep()）。\n\n调试：设置PYTHONASYNCIODEBUG=1环境变量可启用调试模式。\n\n取消任务：被取消的任务会引发CancelledError，需妥善处理。','注意事项 Python版本：部分功能需Python 3.7+（如asyncio.run ）。 阻塞操作：避免在协程中使用同步阻塞代码（如time.sleep ）。 调试：设置PYTHONASYNCIODEBUG=1环境变量可启用调试模式。 取消任务：被取消的任务会引发CancelledError，需',2,3,0,3,'2026-08-27 18:27:56','2026-08-28 14:07:33',0);
/*!40000 ALTER TABLE `article` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `article_tag`
--

DROP TABLE IF EXISTS `article_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `article_tag` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `article_id` bigint NOT NULL,
  `tag_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_article_tag` (`article_id`,`tag_id`)
) ENGINE=InnoDB AUTO_INCREMENT=396 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `article_tag`
--

LOCK TABLES `article_tag` WRITE;
/*!40000 ALTER TABLE `article_tag` DISABLE KEYS */;
INSERT INTO `article_tag` VALUES (5,4,4),(6,5,5),(7,6,6),(8,6,7),(9,7,8),(394,9,1),(12,10,5),(11,10,7),(395,481,8);
/*!40000 ALTER TABLE `article_tag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `category`
--

DROP TABLE IF EXISTS `category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `category` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `category`
--

LOCK TABLES `category` WRITE;
/*!40000 ALTER TABLE `category` DISABLE KEYS */;
INSERT INTO `category` VALUES (1,'技术','2026-05-28 15:01:36'),(2,'生活','2026-05-28 15:01:36'),(3,'随笔','2026-05-28 15:01:36'),(4,'教程','2026-05-28 15:01:36');
/*!40000 ALTER TABLE `category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comment`
--

DROP TABLE IF EXISTS `comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `content` text NOT NULL,
  `article_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `parent_id` bigint DEFAULT NULL COMMENT '父评论ID，NULL为顶级评论',
  `reply_user_id` bigint DEFAULT NULL COMMENT '被回复用户ID',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted` tinyint NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_article_id` (`article_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_parent_id` (`parent_id`)
) ENGINE=InnoDB AUTO_INCREMENT=294 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comment`
--

LOCK TABLES `comment` WRITE;
/*!40000 ALTER TABLE `comment` DISABLE KEYS */;
INSERT INTO `comment` VALUES (1,'写得很清楚，感谢分享！',1,2,NULL,NULL,'2026-05-28 17:04:56',1),(2,'正好在学 Spring Boot，收藏了！',1,3,NULL,NULL,'2026-05-28 17:04:56',1),(3,'谢谢支持，后续会更新更多内容。',1,1,1,2,'2026-05-28 17:04:56',1),(4,'期待进阶篇！',1,2,2,3,'2026-05-28 17:04:56',1),(5,'组合式 API 确实比 Options API 灵活多了。',2,3,NULL,NULL,'2026-05-28 17:04:56',1),(6,'能详细讲讲 provide/inject 吗？',2,2,NULL,NULL,'2026-05-28 17:04:56',1),(7,'好的，下一篇会专门讲这个。',2,1,6,2,'2026-05-28 17:04:56',1),(8,'年终总结写得好充实！',3,1,NULL,NULL,'2026-05-28 17:04:56',0),(9,'新年快乐！一起加油！',3,3,NULL,NULL,'2026-05-28 17:04:56',0),(10,'联合索引的最左前缀原则讲得很透彻。',4,3,NULL,NULL,'2026-05-28 17:04:56',0),(11,'实际项目中遇到过索引失效的问题。',4,2,10,3,'2026-05-28 17:04:56',0),(12,'async/await 真的是 JS 的救星！',5,2,NULL,NULL,'2026-05-28 17:04:56',0),(13,'Python 做数据分析确实方便。',7,2,NULL,NULL,'2026-05-28 17:04:56',0),(14,'能推荐一些学习资源吗？',7,3,NULL,NULL,'2026-05-28 17:04:56',0),(15,'《代码整洁之道》确实是必读书籍。',9,3,NULL,NULL,'2026-05-28 17:04:56',0),(16,'谢谢！',3,2,8,1,'2026-05-31 14:18:54',1),(18,'11',12,2,NULL,NULL,'2026-06-01 22:02:49',1),(19,'22',12,2,18,2,'2026-06-01 22:02:57',1),(23,'你好啊',12,2,22,4,'2026-06-03 16:06:58',1),(25,'1',9,2,NULL,NULL,'2026-06-03 20:03:05',1),(26,'2',9,2,NULL,NULL,'2026-06-03 20:03:11',1),(27,'1',15,2,NULL,NULL,'2026-06-03 20:09:45',1),(28,'1',15,2,NULL,NULL,'2026-06-03 20:14:55',1),(32,'33',10,2,31,5,'2026-06-16 20:33:21',1),(34,'管理员回复：感谢评论！',94,1,33,6,'2026-07-31 16:52:13',1),(292,'谢谢分享',4,3,NULL,NULL,'2026-08-28 16:06:19',0),(293,'写得真好！',10,2,NULL,NULL,'2026-08-30 23:04:31',0);
/*!40000 ALTER TABLE `comment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notification`
--

DROP TABLE IF EXISTS `notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notification` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL COMMENT '接收通知的用户ID',
  `from_user_id` bigint NOT NULL COMMENT '触发通知的用户ID',
  `type` varchar(20) NOT NULL COMMENT '通知类型: comment/favorite/reply',
  `content` varchar(500) NOT NULL COMMENT '通知内容',
  `article_id` bigint DEFAULT NULL COMMENT '关联文章ID',
  `is_read` tinyint(1) DEFAULT '0' COMMENT '是否已读 0-未读 1-已读',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_read` (`user_id`,`is_read`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notification`
--

LOCK TABLES `notification` WRITE;
/*!40000 ALTER TABLE `notification` DISABLE KEYS */;
/*!40000 ALTER TABLE `notification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `read_history`
--

DROP TABLE IF EXISTS `read_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `read_history` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `article_id` bigint NOT NULL,
  `read_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_article` (`user_id`,`article_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_article_id` (`article_id`)
) ENGINE=InnoDB AUTO_INCREMENT=440 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `read_history`
--

LOCK TABLES `read_history` WRITE;
/*!40000 ALTER TABLE `read_history` DISABLE KEYS */;
INSERT INTO `read_history` VALUES (28,2,9,'2026-06-15 23:56:25'),(35,4,10,'2026-06-16 16:29:05'),(40,4,8,'2026-06-03 15:48:20'),(41,4,3,'2026-06-03 16:59:58'),(44,4,4,'2026-06-03 15:49:57'),(45,4,6,'2026-06-03 15:50:01'),(63,4,9,'2026-06-03 17:06:04'),(70,2,7,'2026-08-27 19:36:31'),(73,2,10,'2026-08-27 18:04:38'),(83,2,5,'2026-06-09 16:54:01'),(100,1,10,'2026-06-16 16:06:55'),(107,5,10,'2026-06-16 16:29:31'),(109,2,3,'2026-08-24 20:14:25'),(274,3,10,'2026-08-25 17:43:37'),(305,2,1,'2026-08-25 17:51:06'),(306,2,4,'2026-08-27 19:45:40'),(308,3,1,'2026-08-25 17:46:14'),(309,3,4,'2026-08-28 16:06:05'),(413,1,1,'2026-08-26 17:47:22'),(414,1,4,'2026-08-26 16:01:30'),(416,1,6,'2026-08-26 16:03:22'),(419,1,9,'2026-08-26 17:13:19'),(425,3,5,'2026-08-26 22:56:05'),(432,2,481,'2026-08-27 18:20:50'),(434,2,483,'2026-08-27 19:36:11'),(437,2,8,'2026-08-27 19:45:38');
/*!40000 ALTER TABLE `read_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tag`
--

DROP TABLE IF EXISTS `tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tag` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tag`
--

LOCK TABLES `tag` WRITE;
/*!40000 ALTER TABLE `tag` DISABLE KEYS */;
INSERT INTO `tag` VALUES (1,'Java','2026-05-28 15:01:36'),(2,'Vue','2026-05-28 15:01:36'),(3,'Spring Boot','2026-05-28 15:01:36'),(4,'MySQL','2026-05-28 15:01:36'),(5,'JavaScript','2026-05-28 15:01:36'),(6,'CSS','2026-05-28 15:01:36'),(7,'HTML','2026-05-28 15:01:36'),(8,'Python','2026-05-28 15:01:36');
/*!40000 ALTER TABLE `tag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `nickname` varchar(50) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `avatar` varchar(500) DEFAULT NULL,
  `bio` varchar(500) DEFAULT NULL COMMENT '个人简介',
  `role` varchar(20) NOT NULL DEFAULT 'USER' COMMENT 'USER/ADMIN',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted` tinyint NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=251 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (1,'admin','$2a$10$pv8ltIkrii2yzu/gdQ5/k.pI7rmvPtjVtvI4hHrN0Gjwz03j8B22y','管理员','admin@blog.com',NULL,NULL,'ADMIN','2026-05-28 17:04:56','2026-08-28 17:18:29',0),(2,'zhangsan','$2a$10$9Uj4TgBYExEYlCybIzg/WOJ/lS.IH9LAou5rnua3LS2MCgC0XG0JW','新的昵称','new@email.com','https://c-ssl.dtstatic.com/uploads/blog/202205/31/20220531134105_e1591.thumb.400_0.jpg','这是新的个人简介','USER','2026-05-28 17:04:56','2026-08-25 18:17:24',0),(3,'lisi','$2a$10$UGwYpbGb1sGKgeiqvg1MwOs28geR0UP3QRu/wCX2BjsI94sz6QSZS','李四','lisi@example.com',NULL,NULL,'USER','2026-05-28 17:04:56','2026-05-28 17:04:56',0),(249,'testuser','$2a$10$8FF.eaWKnn08YO9CJLSjgeytdoYRs16nFFsKOY81Z1kYC691xIPca','testuser',NULL,NULL,NULL,'USER','2026-09-05 02:10:47','2026-09-05 02:10:47',0),(250,'noar','$2b$10$UyPYe0aQfgejq3RpGhXn9u1k.EH/l4WtuNpkDblHemmtebLIHSkeu',NULL,NULL,NULL,NULL,'USER','2026-09-05 00:00:00','2026-09-05 00:00:00',0);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_favorite`
--

DROP TABLE IF EXISTS `user_favorite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_favorite` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `article_id` bigint NOT NULL,
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_article` (`user_id`,`article_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_article_id` (`article_id`)
) ENGINE=InnoDB AUTO_INCREMENT=109 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_favorite`
--

LOCK TABLES `user_favorite` WRITE;
/*!40000 ALTER TABLE `user_favorite` DISABLE KEYS */;
INSERT INTO `user_favorite` VALUES (1,2,10,'2026-05-31 19:24:14');
/*!40000 ALTER TABLE `user_favorite` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'blog_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-09-05  2:10:51
