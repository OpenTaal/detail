if [ ! -e .database-username -a ! -e .database-password ]
then
	echo ERROR: Missing file .database-username and/or .database-password
	exit 1
fi
DATABASE=opentaal
if [ -e details.xml.bz2 ]
then
	bunzip2 -f details.xml.bz2
fi
mysql $DATABASE -u `cat .database-username` -p`cat .database-password` --silent -e "DROP TABLE IF EXISTS details"
mysql $DATABASE -u `cat .database-username` -p`cat .database-password` --silent -e "CREATE TABLE details(word VARCHAR(75) NOT NULL PRIMARY KEY, next_version CHAR(1) NOT NULL, 2_10 CHAR(1) NOT NULL, 2_00 CHAR(1) NOT NULL, 1_10 CHAR(1) NOT NULL, 1_00 CHAR(1) NOT NULL, ntg1996 VARCHAR(1) NOT NULL, egb TINYINT(4), base_word VARCHAR(75) NOT NULL, alternatief VARCHAR(75) NOT NULL, woordtype VARCHAR(256) NOT NULL, exclude_spell_checker TINYINT(1) NOT NULL, temporal_qualifier TINYINT(1) NOT NULL, INDEX word(word))"
if [ -e details.xml ]
then
	mysql $DATABASE -u `cat .database-username` -p`cat .database-password` --local_infile=1 --silent -e "LOAD XML LOCAL INFILE 'details.xml' INTO TABLE details"
else
	echo ERROR: Missing file details.xml
	exit 1
fi
