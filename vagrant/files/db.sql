CREATE DATABASE IF NOT EXISTS `auth`;

USE `auth`;

CREATE TABLE IF NOT EXISTS `group` (
  `id`       BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`     VARCHAR(255)        NOT NULL,
  `gid`      INT(10) UNSIGNED    NOT NULL,
  `password` VARCHAR(255)        NOT NULL DEFAULT '!',
  PRIMARY KEY (`id`)
)
  ENGINE = InnoDB
  DEFAULT CHARSET = utf8;

CREATE TABLE IF NOT EXISTS `grouplist` (
  `id`       BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(255)        NOT NULL,
  `gid`      INT(10) UNSIGNED    NOT NULL,
  PRIMARY KEY (`id`)
)
  ENGINE = InnoDB
  DEFAULT CHARSET = utf8;


CREATE TABLE IF NOT EXISTS `user` (
  `id`       BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(255)        NOT NULL,
  `gid`      INT(10) UNSIGNED    NOT NULL,
  `uid`      INT(10) UNSIGNED    NOT NULL,
  `gecos`    VARCHAR(255)        NOT NULL DEFAULT '',
  `homedir`  VARCHAR(255)        NOT NULL DEFAULT '',
  `shell`    VARCHAR(255)        NOT NULL DEFAULT '',
  `password` VARCHAR(255)        NOT NULL DEFAULT '!',
  `lstchg`   BIGINT(20) UNSIGNED NOT NULL,
  `mini`     BIGINT(20)          NOT NULL DEFAULT '0',
  `maxi`     BIGINT(20)          NOT NULL DEFAULT '99999',
  `warn`     BIGINT(20)          NOT NULL DEFAULT '7',
  `inact`    BIGINT(20)          NOT NULL DEFAULT '-1',
  `expire`   BIGINT(20)          NOT NULL DEFAULT '-1',
  `flag`     INT(11)             NOT NULL DEFAULT '-1',
  PRIMARY KEY (`id`)
)
  ENGINE = InnoDB
  DEFAULT CHARSET = utf8;