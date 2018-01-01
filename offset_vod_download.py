#!/usr/bin/env python
#
# Given INI file, uses FFMPEG to download, possibly part, of audio-video VOD|stream|file.
# Input URL must point to FFMPEG compatible AV format media.
# All input and out parameters must be specified through input INI file.
#
# INPUT
# ----------------
# --iini FILE  --  Input INI file.
#        Following global entries are recognized:
#            url2, dir2, fnm2, pos2, len2
#        Only 'url2' entry is required other are optional and will be default assigned.
#        Hash-tag character can be used for commnets (relaxed to lines starting with
#        any non-word character).
#        Entry 'fnm2' can have timestamp tag as "{TS2}" token that gets replaced with
#        current timestamp, eg: "5A4956AE".
#
#        Example:
#            url2 = https://example.com/videostream=HmpsfnV3tTwW
#            dir2 = /tmp
#            fnm2 = outp.mkv
#            pos2 = 0:15:00
#            len2 = 0:00:10
#
# "path.cfg" - File in the same directory this .py file is in, if exists,
#              first line path is added to the PATH environment variable.
#              If first line is a path to existing file, it is assumed to be ffmpeg
#              executable itself, and is used.
#
import os, sys, optparse, time, datetime
import re   ## Regex
import subprocess

g1z      = type("", (), {"group": (lambda self,g: ""),} )()
szFfm    = "ffmpeg"

## banner
print("\n%s v1.0\n\n" % (os.path.basename(__file__).upper().replace(".","_"),) ),

szPathTxtFn = ("%s/path.cfg" % (os.path.dirname(__file__),))
if( os.path.isfile(szPathTxtFn) ):
	ln0 = os.path.expandvars( open(szPathTxtFn).read(1024).splitlines()[0].strip() )
	if( os.path.isfile(ln0) ):
		szFfm = ln0
	elif( len(ln0) ):
		os.environ["PATH"] = ("%s%s%s" % (ln0, os.pathsep, os.getenv("PATH"),) )

def spi_ShellExecGetText( szCmd ):
	szStd = ""
	try:
		szStd = subprocess.check_output( szCmd, shell=1 )
	except:
		pass
	return szStd

szStd = spi_ShellExecGetText( ("%s -version" % (szFfm,) ) )
sz2 = ( ( re.search("ffmpeg \\s+ version \\s+ ([^\\s]+)", szStd, re.I|re.X ) or g1z ).group(1) )
print("Using FFMPEG version: [%s]" % (sz2,) )

if( not len(sz2) ):
	print("ERROR: no working ffmpeg executable found.")
	print("       [%s]" % (szFfm,) )
	sys.exit(2)


prsr = optparse.OptionParser()
prsr.add_option("--iini", dest="iini", help="Input INI file.")
(optns, args) = prsr.parse_args()
szIni = ( optns.iini if optns.iini else "" )

if( not len(szIni) ):
	for i in range( 0, len(args) ):
		a = args[i]
		ext2 = (os.path.splitext(a)[1]).lower().lstrip(".")
		if( ext2 == "ini" ):
			szIni = a
			break

if( not len(szIni) ):
	print("ERROR: no input INI (see --iini).")
	sys.exit(3)
if( not os.path.isfile(szIni) ):
	print("ERROR: input INI file not found.")
	print("       [%s]" % (szIni,) )
	sys.exit(4)

print("Input INI file: [...%s]" % (szIni[-42:],))
ini2 = filter( (lambda a: a != ""), open(szIni).read(65536).splitlines() )
print("Got %d lines." % (len(ini2),))
ini3 = {"url2": "", "dir2": "", "fnm2": "", "pos2": "", "len2": "", }
for i in range( 0, len(ini2) ):
	a = ini2[i]
	vnm = ( ( re.search("^\\s*([\\w]+)\\s*\\=", a, re.I|re.X ) or g1z ).group(1) )
	val = ( ( re.search("\\=(.+)", a, re.I|re.X ) or g1z ).group(1) ).strip().strip("\x22\x27")
	if( len(vnm) ):
		ini3[vnm] = val


if( not len(ini3["url2"]) ):
	print("ERROR: no URL in input INI file (url2 entry is required).")
	sys.exit(5)

if( not len(ini3["pos2"]) ):
	ini3["pos2"] = "0:00:00"

if( not len(ini3["dir2"]) ):
	ini3["dir2"] = os.path.dirname(szIni)
	if( len(ini3["dir2"]) ):
		print("INFO: auto output dir, assigned from input INI dir-name.")
		print("      [...%s]" % (ini3["dir2"][-42:],) )


if( not len(ini3["fnm2"]) ):
	bnm = os.path.splitext( os.path.basename(szIni) )[0]
	if( len(bnm) ):
		secs2 = int(round(time.time() * 1000)) / 1000
		ini3["fnm2"] = ("%s_o%X.mkv" % (bnm, secs2 ) )
		if( len( ini3["fnm2"] ) ):
			print("INFO: auto output filename, assigned from input INI [%s]" % (ini3["fnm2"],))

if( len(ini3["fnm2"]) ):
	secs3 = int(round(time.time() * 1000)) / 1000
	ini3["fnm2"] = ini3["fnm2"].replace("{TS2}", ("%X" % (secs3,)) )

if( not len(ini3["fnm2"]) ):
	print("ERROR: no output file-name from INI.")
	sys.exit(7)

if( not len(ini3["dir2"]) ):
	print("ERROR: no output dir-name from INI.")
	sys.exit(8)

if 1:
	print("\n"+"Parsed INI preview:")
	ini4 = ini3.items()
	for i in range( 0, len(ini4) ):
		a = ini4[i]
		print("\t%-8s: [%s%s]" % ( a[0], ("..." if len(a[1][42:]) else ""), a[1][-42:],))

if 1:
	ofn3 = ("%s/%s" % ( ini3["dir2"], ini3["fnm2"],) )
	if( os.path.isfile(ofn3) ):
		print("ERROR: output file already exists.")
		print("       [%s]" % (ofn3,) )
		sys.exit(9)
	## ffmpeg -ss 3:00:00 -i "$url2" -c copy -t 1:00:00 "$dir2/$bnm2"
	cmd2 = ("%s -hide_banner -ss %s -i %s -c copy%s %s" % (
			("\x22%s\x22" % szFfm ),
			ini3["pos2"],
			("\x22%s\x22" % ini3["url2"] ),
			( (" -t %s" % (ini3["len2"],)) if len(ini3["len2"]) else "" ),
			( "\x22%s\x22" % (ofn3,) ),
			))
	if 1:
		cmd3 = cmd2
		cmd3 = re.sub("(http[s]?://[^\\x22\\x20]{,24})[^\\x22\\x20]+", "\\1", cmd3, 0, re.I|re.X )
		cmd3 = re.sub("/\\w+/\\w+/[^\\x22\\x20]+", (lambda a: "..."+a.group(0)[-24:]), cmd3, 0, re.I|re.X )
		print("\n"+"CMD: [%s]" % (cmd3,))
		raw_input("\n"+"Press enter to Continue . . .")
		print("Running FFMPEG ...\n\n"),
		del cmd3

	rs2 = subprocess.call( cmd2, shell=1 )
	if rs2:
		print("ERROR: FFMPEG failed, code:%d." % (rs2,) )
		sys.exit(rs2)

print("Done.")










