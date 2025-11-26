# Godliness
## A generalised custom folder cleanup tool

This program is designed to allow a user to easily schedule folder cleanups to keep our acctual data storage periods in line with GDPR and data retention policys/laws.

This consists of 2 parts, connected via a database table.

The table contains a list of filepaths along with each filepath's retention time, targeted file suffix/es and excluded filename/s, along with an associated client name for admin purposes.

The first program, Godliness, goes through the list of filepaths and for each one deletes all files older than the retention time in days. If a file suffix/list of file suffixes is provided, it will only delete files with that/those suffix/es. If any excluded filenames are provided they will be ignored.

The second program, Godliconfig, allows a non-SQL user to perform the full suite of CRUD (Create, Read, Update, Delete) actions to the database table. This allows non-IS users to alter which folders are checked/files deleted. This is still restricted to the Tech team, as this process could be highly destructive.

There is also a script (Godlifolderchecker.py) that goes through some of our default import/export folders and checks for processed/done folders that are not in the configuration list.
