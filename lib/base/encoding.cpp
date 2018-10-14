#include <cstdio>
#include <cstdlib>
#include <lib/base/cfile.h>
#include <lib/base/encoding.h>
#include <lib/base/eerror.h>
#include <lib/base/eenv.h>
#include <uchardet/uchardet.h>

eDVBTextEncodingHandler encodingHandler;  // the one and only instance
int defaultEncodingTable = 1;   // the one and only instance

inline char tolower(char c)
{
	return (c >= 'A' && c <= 'Z') ? c + ('a' - 'A') : c;
}

int detectEncoding(const std::string &content, std::string &encoding)
{
	uchardet_t handle = uchardet_new();
	int retval = uchardet_handle_data(handle, content.c_str(), content.length());
	if (retval == 0)
	{
		uchardet_data_end(handle);
		encoding = uchardet_get_charset(handle);
		uchardet_delete(handle);
	}
	return retval;
}

int mapEncoding(char *s_table)
{
	int encoding = -1;
	int no_table_id = 0;

	//if encoding string has a option 'N' or 'NOID' first split by ':' , it indicates that the string has no
	//     encoding id char in the first byte, and the bit 0x80 of encoding id will be set.
	char *colon=strrchr(s_table, ':');
	if(colon != NULL){
		if(strncmp(s_table,"n:",2) == 0 || strncmp(s_table,"noid:",5) == 0 )
			no_table_id = NOTABLEID;
		s_table = colon + 1;
	}

	// table name will be in lowercase!
	if (sscanf(s_table, "iso8859-%d", &encoding) == 1)
		return no_table_id | encoding;
	if (sscanf(s_table, "iso%d", &encoding) == 1 and encoding == 6937)
		return no_table_id;
	if (strcmp(s_table, "gb2312") == 0 || strcmp(s_table, "gbk") == 0
		|| strcmp(s_table, "gb18030") == 0 || strcmp(s_table, "cp936") == 0)
		return no_table_id | GB18030_ENCODING;
	if (strcmp(s_table, "big5") == 0 || strcmp(s_table, "cp950") == 0)
		return no_table_id | BIG5_ENCODING;
	if (strcmp(s_table, "utf8") == 0 || strcmp(s_table, "utf-8") == 0)
		return no_table_id | UTF8_ENCODING;
	if (strcmp(s_table, "unicode") == 0)
		return no_table_id | UNICODE_ENCODING;
	if (strcmp(s_table, "utf16be") == 0)
		return no_table_id | UTF16BE_ENCODING;
	if (strcmp(s_table, "utf16le") == 0)
		return no_table_id | UTF16LE_ENCODING;
	else
		eDebug("[eDVBTextEncodingHandler] unsupported table in encoding.conf: %s. ", s_table);
	return -1;
}

eDVBTextEncodingHandler::eDVBTextEncodingHandler()
{
	std::string file = eEnv::resolve("${sysconfdir}/enigma2/encoding.conf");
	if (::access(file.c_str(), R_OK) < 0)
	{
		/* no personalized encoding.conf, fallback to the system default */
		file = eEnv::resolve("${datadir}/enigma2/encoding.conf");
	}
	CFile f(file.c_str(), "rt");

	if (f)
	{
		size_t bufsize = 256;
		char *line = (char*) malloc(bufsize);
		char countrycode[bufsize];
		char *s_table = (char*) malloc(bufsize);
		while (getline(&line, &bufsize, f) != -1)
		{
			int i, j = 0;	   // remove leading whitespace and control chars, and comments
			for (i = 0; line[i]; i++) {
				if (line[i] == '#')
					break; // skip rest of line
				if (j == 0 && line[i] > 0 && line[i] <= ' ')
					continue;       //skip non-printable char and whitespace in head
				line[j++] = tolower(line[i]); // countrycodes are always lowercase, same as are used in event and epgcache !
			}
			if (j == 0)
				continue;       // skip 'empty' lines
			line[j] = 0;

			int tsid, onid, encoding = -1;
			if (sscanf(line, "0x%x 0x%x %s", &tsid, &onid, s_table) == 3
				  || sscanf(line, "%d %d %s", &tsid, &onid, s_table) == 3 ) {
				encoding = mapEncoding(s_table);
				if (encoding != -1)
					m_TransponderDefaultMapping[(tsid<<16)|onid] = encoding;
			}
			else if (sscanf(line, "0x%x 0x%x", &tsid, &onid) == 2
					|| sscanf(line, "%d %d", &tsid, &onid) == 2 ) {
				m_TransponderUseTwoCharMapping.insert((tsid<<16)|onid);
				encoding = 0; // avoid spurious error message
			}
			else if (sscanf(line, "%s %s", countrycode, s_table) == 2 ) {
				encoding = mapEncoding(s_table);
				if (encoding != -1) {
					if (countrycode[0] == '*')
						defaultEncodingTable = encoding;
					else
						m_CountryCodeDefaultMapping[countrycode] = encoding;
				}
			}

			if (encoding == -1)
				eDebug("[eDVBTextEncodingHandler] encoding.conf: couldn't parse %s", line);
		}
		free(line);
		free(s_table);
	}
	else
		eDebug("[eDVBTextEncodingHandler] couldn't open %s: %m", file.c_str());
}

void eDVBTextEncodingHandler::getTransponderDefaultMapping(int tsidonid, int &table)
{
	std::map<int, int>::iterator it =
		m_TransponderDefaultMapping.find(tsidonid);
	if ( it != m_TransponderDefaultMapping.end() )
		table = it->second;
}

bool eDVBTextEncodingHandler::getTransponderUseTwoCharMapping(int tsidonid)
{
	return m_TransponderUseTwoCharMapping.find(tsidonid) != m_TransponderUseTwoCharMapping.end();
}

int eDVBTextEncodingHandler::getCountryCodeDefaultMapping( const std::string &country_code )
{
	std::map<std::string, int>::iterator it =
		m_CountryCodeDefaultMapping.find(country_code);
	if ( it != m_CountryCodeDefaultMapping.end() )
		return it->second;
	return defaultEncodingTable;
}