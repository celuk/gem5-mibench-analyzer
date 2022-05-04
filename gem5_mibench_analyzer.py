import os
import subprocess
import re

gem5path = "/Users/shc/gem5"
gem5buildoptpath = gem5path + "/build/RISCV/gem5.opt"

exec = "hello"
gem5outdir = "/Users/shc/gem5/m5out/"
gem5optoptions = " --debug-flags=Exec,Decode --debug-file=exectrace.txt"
gem5configpath = gem5path + "/configs/example/se.py"
execpath = "/Users/shc/mibenchriscv/"
execcmd = execpath + exec

execoptions = "" # " --options='/Users/shc/mibenchriscv/input_large.dat' " # exec pathin bi eksigi + large.dat
gem5confoptions = "--data-trace-file=datatrace.gz --inst-trace-file=insttrace.gz"

# default cpu type cachesiz atomicsimplecpu
otherconfoptions = "" # " --maxinsts=1000000 --cpu-type=DerivO3CPU --bp-type=BiModeBP --mem-type=DDR4_2400_16x4 --mem-size=4GB --caches --l1i_size=4kB --l1i_assoc=8 --l1d_size=4kB --l1d_assoc=8 --l2cache --l2_size=128kB --l2_assoc=4 "

gem5cmd = gem5buildoptpath + " " + "--outdir=" + gem5outdir + exec + gem5optoptions + " " + gem5configpath + " -c " + execcmd + execoptions + " " + gem5confoptions + otherconfoptions

mibenchpath = "/Users/shc/mibenchriscv"

# riscv64-unknown-elf-objcopy -O binary dene.elf dene.bin
riscvtoolpath = "/usr/local/Cellar/riscv-gnu-toolchain/main/bin/"
riscvobjcp = riscvtoolpath + "riscv64-unknown-elf-objcopy"
riscvobjcpbin = riscvobjcp + " -O binary " #+ exec + " " + exec + ".bin"

riscvobjdmp = riscvtoolpath + "riscv64-unknown-elf-objdump"
riscvobjdis = riscvobjdmp + " -d "

# python3 /Users/shc/gem5/util/decode_packet_trace.py system.cpu.traceListener.datatrace.gz outdatatrace.txt
pyexec = "python3"
decodepypath = " " + gem5path + "/util/decode_packet_trace.py "

def decodeinstdatatraces():
	decodecmd = pyexec + decodepypath + gem5outdir + "/system.cpu.traceListener.datatrace.gz " + gem5outdir + "/outdatatrace.txt"
	print(decodecmd)
	result = subprocess.getoutput(decodecmd)
	print(result)

	decodecmd = pyexec + decodepypath + gem5outdir + "/system.cpu.traceListener.insttrace.gz " + gem5outdir + "/outinsttrace.txt"
	print(decodecmd)
	result = subprocess.getoutput(decodecmd)
	print(result)

def getstaticdis():
	global exec
	exec = "/" + execcmd.rpartition('/')[-1]

	disFile = gem5outdir + exec + "_disassembled.txt"
	objdiscmd = riscvobjdis + execcmd + " > " + disFile
	print(objdiscmd)
	result = subprocess.getoutput(objdiscmd)
	print(result)

def getstatichex():
	global exec
	exec = "/" + execcmd.rpartition('/')[-1]

	binFile = gem5outdir + exec + ".bin"
	objcpcmd = riscvobjcpbin + execcmd + " " + binFile
	print(objcpcmd)
	result = subprocess.getoutput(objcpcmd)
	print(result)

	with open(binFile, "rb") as f:
		binData = f.read()
	
	hexFileName = gem5outdir + exec + "_static.hex"
	hexFile = open(hexFileName, 'w')

	while (i < len(binData) // 4):
		w = binData[4*i : 4*i+4]
		hexFile.write("%02x%02x%02x%02x" % (w[3], w[2], w[1], w[0]))
		hexFile.write("\n")
	
	hexFile.close()

# bu fonka yuzdelik random secimler eklenebilir ve onlar ayri memtrace.txtler olarak basilabilir.
# su an %100
def getmemtrace():
	traceFileName = gem5outdir + "/exectrace.txt"
	traceFile = open(traceFileName, 'r')
	traceLines = traceFile.readlines()

	prevInstCount = 0
	validDistance = 0

	lineCount = 0
	eachLine = ""

	memTraceFileName = gem5outdir + "/memtrace.txt"
	memTraceFile = open(memTraceFileName, 'w')

	memTraceFileNameSys = gem5outdir + "/memtrace_syscallsiz.txt"
	memTraceFileSys = open(memTraceFileNameSys, 'w')

	for line in traceLines:
		eachLine += line + ' '
		lineCount += 1

		if 'T0' in line:
			if lineCount == 5:
				opr = re.search('(?:[^:]*:){15} (.+?):', eachLine).group(1).rstrip().lstrip()
			else:
				opr = re.search('(?:[^:]*:){13} (.+?):', eachLine).group(1).rstrip().lstrip()
			addr = eachLine.partition("A=")[2].rstrip().lstrip()
			inst = re.search('Decoding instruction (.*) at', eachLine).group(1).rstrip().lstrip()
			pc = re.search('T0 : (.+?) @', eachLine).group(1).rstrip().lstrip()

			if opr == 'MemRead':
				memTraceFile.write(prevInstCount.__str__() + ' ' + addr + ' R\n')
				memTraceFileSys.write(prevInstCount.__str__() + ' ' + addr + ' R\n')
				prevInstCount = 0
			elif opr == 'MemWrite':
				memTraceFile.write(prevInstCount.__str__() + ' ' + addr + ' W\n')
				memTraceFileSys.write(prevInstCount.__str__() + ' ' + addr + ' W\n')
				prevInstCount = 0
			#else:
			#	prevInstCount = prevInstCount + 1

			# Vler arasi uzaklik | adres | veri | V
			memTraceFile.write(validDistance.__str__() + ' ' + pc + ' ' + inst + ' V\n')
			if opr != 'No_OpClass': # syscallari ele
				memTraceFileSys.write(validDistance.__str__() + ' ' + pc + ' ' + inst + ' V\n')

			prevInstCount = 0
			validDistance = 0
			lineCount = 0
			eachLine = ""

	traceFile.close()
	memTraceFile.close()
	memTraceFileSys.close()

pathlist = []

for (path, dirs, files) in os.walk(mibenchpath):
	for f in files:
		try:
			filecmdoutput = subprocess.getoutput("file " + path + '/' + f)
			if filecmdoutput.__str__().__contains__("ELF 64-bit LSB executable, UCB RISC-V") and not path.__contains__("000") :
				pathlist.append(path)
		except: 
			pass

pathlist = list(set(pathlist))
#print(*pathlist, sep='\n')

gem5outdirlist = []
execlist = []
execoptionlist = []

for eachpath in pathlist:
	if eachpath.endswith("qsort"):
		gem5outdirlist.append(gem5outdir + "qsort/qsort_small")
		execlist.append(eachpath + "/qsort_small")
		execoptionlist.append(eachpath + "/input_small.dat")

		gem5outdirlist.append(gem5outdir + "qsort/qsort_large")
		execlist.append(eachpath + "/qsort_large")
		execoptionlist.append(eachpath + "/input_large.dat")
	elif eachpath.endswith("jpeg-6a"):
		upperdir = eachpath.rsplit('/', 1)[0]

		gem5outdirlist.append(gem5outdir + "jpeg/jpeg_small/cjpeg_small")
		execlist.append(eachpath + "/cjpeg")
		execoptionlist.append("-dct int -progressive -opt -outfile " + gem5outdirlist[-1] + "/output_small_encode.jpeg " + upperdir + "/input_small.ppm")
		
		gem5outdirlist.append(gem5outdir + "jpeg/jpeg_small/djpeg_small")
		execlist.append(eachpath + "/djpeg")
		execoptionlist.append("-dct int -ppm -outfile " + gem5outdirlist[-1] + "/output_small_decode.ppm " + upperdir + "/input_small.jpg")

		gem5outdirlist.append(gem5outdir + "jpeg/jpeg_large/cjpeg_large")
		execlist.append(eachpath + "/cjpeg")
		execoptionlist.append("-dct int -progressive -opt -outfile " + gem5outdirlist[-1] + "/output_large_encode.jpeg " + upperdir + "/input_large.ppm")
		
		gem5outdirlist.append(gem5outdir + "jpeg/jpeg_large/djpeg_large")
		execlist.append(eachpath + "/djpeg")
		execoptionlist.append("-dct int -ppm -outfile " + gem5outdirlist[-1] + "/output_large_decode.ppm " + upperdir + "/input_large.jpg")
	elif eachpath.endswith("sha"):
		gem5outdirlist.append(gem5outdir + "sha/sha_small")
		execlist.append(eachpath + "/sha")
		execoptionlist.append(eachpath + "/input_small.asc")

		gem5outdirlist.append(gem5outdir + "sha/sha_large")
		execlist.append(eachpath + "/sha")
		execoptionlist.append(eachpath + "/input_large.asc")
	elif eachpath.endswith("FFT"):
		gem5outdirlist.append(gem5outdir + "FFT/FFT_small/fft_small")
		execlist.append(eachpath + "/fft")
		execoptionlist.append("4 4096")

		gem5outdirlist.append(gem5outdir + "FFT/FFT_small/fft_small_inv")
		execlist.append(eachpath + "/fft")
		execoptionlist.append("4 8192 -i") # 8192?

		gem5outdirlist.append(gem5outdir + "FFT/FFT_large/fft_large")
		execlist.append(eachpath + "/fft")
		execoptionlist.append("8 32768")

		gem5outdirlist.append(gem5outdir + "FFT/FFT_large/fft_large_inv")
		execlist.append(eachpath + "/fft")
		execoptionlist.append("8 32768 -i")
	elif eachpath.endswith("stringsearch"):
		gem5outdirlist.append(gem5outdir + "stringsearch/stringsearch_small")
		execlist.append(eachpath + "/search_small")
		execoptionlist.append("")

		gem5outdirlist.append(gem5outdir + "stringsearch/stringsearch_large")
		execlist.append(eachpath + "/search_large")
		execoptionlist.append("")
	elif eachpath.endswith("rijndael"):
		gem5outdirlist.append(gem5outdir + "rijndael/rijndael_small/rijndael_small_enc")
		execlist.append(eachpath + "/rijndael")
		execoptionlist.append(eachpath + "/input_small.asc " + gem5outdirlist[-1] + "/output_small.enc e 1234567890abcdeffedcba09876543211234567890abcdeffedcba0987654321")

		gem5outdirlist.append(gem5outdir + "rijndael/rijndael_small/rijndael_small_dec")
		execlist.append(eachpath + "/rijndael")
		execoptionlist.append(gem5outdirlist[-2] + "/output_small.enc " + gem5outdirlist[-1] + "/output_small.dec d 1234567890abcdeffedcba09876543211234567890abcdeffedcba0987654321")

		gem5outdirlist.append(gem5outdir + "rijndael/rijndael_large/rijndael_large_enc")
		execlist.append(eachpath + "/rijndael")
		execoptionlist.append(eachpath + "/input_large.asc " + gem5outdirlist[-1] + "/output_large.enc e 1234567890abcdeffedcba09876543211234567890abcdeffedcba0987654321")

		gem5outdirlist.append(gem5outdir + "rijndael/rijndael_large/rijndael_large_dec")
		execlist.append(eachpath + "/rijndael")
		execoptionlist.append(gem5outdirlist[-2] + "/output_large.enc " + gem5outdirlist[-1] + "/output_large.dec d 1234567890abcdeffedcba09876543211234567890abcdeffedcba0987654321")
	elif eachpath.endswith("dijkstra"):
		gem5outdirlist.append(gem5outdir + "dijkstra/dijkstra_small")
		execlist.append(eachpath + "/dijkstra_small")
		execoptionlist.append(eachpath + "/input.dat")

		gem5outdirlist.append(gem5outdir + "dijkstra/dijkstra_large")
		execlist.append(eachpath + "/dijkstra_large")
		execoptionlist.append(eachpath + "/input.dat")
	elif eachpath.endswith("bitcount"):
		gem5outdirlist.append(gem5outdir + "bitcount/bitcnts_small")
		execlist.append(eachpath + "/bitcnts")
		execoptionlist.append("75000")

		gem5outdirlist.append(gem5outdir + "bitcount/bitcnts_large")
		execlist.append(eachpath + "/bitcnts")
		execoptionlist.append("1125000")
	elif eachpath.endswith("CRC32"):
		upperdir = eachpath.rsplit('/', 1)[0]

		gem5outdirlist.append(gem5outdir + "CRC32/crc_small")
		execlist.append(eachpath + "/crc")
		execoptionlist.append(upperdir + "/adpcm/data/small.pcm")

		gem5outdirlist.append(gem5outdir + "CRC32/crc_large")
		execlist.append(eachpath + "/crc")
		execoptionlist.append(upperdir + "/adpcm/data/large.pcm")
	elif eachpath.endswith("susan"):
		gem5outdirlist.append(gem5outdir + "susan/susan_small/susan_small_smoothing")
		execlist.append(eachpath + "/susan")
		execoptionlist.append(eachpath + "/input_small.pgm " + gem5outdirlist[-1] + "/output_small.smoothing.pgm -s")

		gem5outdirlist.append(gem5outdir + "susan/susan_small/susan_small_edges")
		execlist.append(eachpath + "/susan")
		execoptionlist.append(eachpath + "/input_small.pgm " + gem5outdirlist[-1] + "/output_small.edges.pgm -e")

		gem5outdirlist.append(gem5outdir + "susan/susan_small/susan_small_corners")
		execlist.append(eachpath + "/susan")
		execoptionlist.append(eachpath + "/input_small.pgm " + gem5outdirlist[-1] + "/output_small.corners.pgm -c")

		gem5outdirlist.append(gem5outdir + "susan/susan_large/susan_large_smoothing")
		execlist.append(eachpath + "/susan")
		execoptionlist.append(eachpath + "/input_large.pgm " + gem5outdirlist[-1] + "/output_large.smoothing.pgm -s")

		gem5outdirlist.append(gem5outdir + "susan/susan_large/susan_large_edges")
		execlist.append(eachpath + "/susan")
		execoptionlist.append(eachpath + "/input_large.pgm " + gem5outdirlist[-1] + "/output_large.edges.pgm -e")

		gem5outdirlist.append(gem5outdir + "susan/susan_large/susan_large_corners")
		execlist.append(eachpath + "/susan")
		execoptionlist.append(eachpath + "/input_large.pgm " + gem5outdirlist[-1] + "/output_large.corners.pgm -c")

	elif eachpath.endswith("basicmath"):
		gem5outdirlist.append(gem5outdir + "basicmath/basicmath_small")
		execlist.append(eachpath + "/basicmath_small")
		execoptionlist.append("")

		gem5outdirlist.append(gem5outdir + "basicmath/basicmath_large")
		execlist.append(eachpath + "/basicmath_large")
		execoptionlist.append("")

	# "< "leri duzelt
	elif eachpath.endswith("src"):
		upperdir = eachpath.rsplit('/', 1)[0]

		gem5outdirlist.append(gem5outdir + "adpcm/adpcm_small/rawcaudio_small")
		execlist.append(eachpath + "/rawcaudio")
		execoptionlist.append("< " + upperdir + "/data/small.pcm")

		gem5outdirlist.append(gem5outdir + "adpcm/adpcm_small/rawdaudio_small")
		execlist.append(eachpath + "/rawdaudio")
		execoptionlist.append("< " + upperdir + "/data/small.adpcm")

		gem5outdirlist.append(gem5outdir + "adpcm/adpcm_large/rawcaudio_large")
		execlist.append(eachpath + "/rawcaudio")
		execoptionlist.append("< " + upperdir + "/data/large.pcm")

		gem5outdirlist.append(gem5outdir + "adpcm/adpcm_large/rawdaudio_large")
		execlist.append(eachpath + "/rawdaudio")
		execoptionlist.append("< " + upperdir + "/data/large.adpcm")


for i in range(0, len(gem5outdirlist) - 1):
	gem5outdir = gem5outdirlist[i]
	execcmd = execlist[i]
	if execoptionlist[i] != "":
		execoptions = " --options='" + execoptionlist[i] + "' "
	else: 
		execoptions = ""
	gem5cmd = gem5buildoptpath + " " + "--outdir=" + gem5outdir + gem5optoptions + " " + gem5configpath + " -c " + execcmd + execoptions + " " + gem5confoptions + otherconfoptions

	print(gem5cmd)
	result = subprocess.getoutput(gem5cmd)
	print(result)
	try:
		getmemtrace()

		decodeinstdatatraces()

		getstatichex()

		getstaticdis()
	except: 
		pass

	print("")
