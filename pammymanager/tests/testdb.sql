DROP TABLE IF EXISTS `group`;

CREATE TABLE `group` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `gid` int(10) unsigned NOT NULL,
  `password` varchar(255) NOT NULL DEFAULT '!',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `grouplist`;

CREATE TABLE `grouplist` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `gid` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `user`;

CREATE TABLE `user` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `gid` int(10) unsigned NOT NULL,
  `uid` int(10) unsigned NOT NULL,
  `gecos` varchar(255) NOT NULL DEFAULT '',
  `homedir` varchar(255) NOT NULL,
  `shell` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL DEFAULT '!',
  `lstchg` bigint(20) unsigned NOT NULL,
  `mini` bigint(20) NOT NULL DEFAULT '0',
  `maxi` bigint(20) NOT NULL DEFAULT '99999',
  `warn` bigint(20) NOT NULL DEFAULT '7',
  `inact` bigint(20) NOT NULL DEFAULT '-1',
  `expire` bigint(20) NOT NULL DEFAULT '-1',
  `flag` int(11) NOT NULL DEFAULT '-1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;