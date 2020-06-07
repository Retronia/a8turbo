import sys
import turbo_data
from a8cas import a8cas 

# generate the sectors containing the XEX data
def blocks(d):
	bn=0
	left=len(d)

	while left>=128:
		b = [0x55, 0x55, 0xFC] + [ord(x) for x in d[bn*128:bn*128+128]] + [(bn + 12)&255, (bn + 12)>>8]
		left -= 128
		bn += 1
		yield b

	if left>0:
		d = d[bn*128:]
		b = [0x55, 0x55, 0xFA] + [ord(x) for x in d] + [0x00]*(127-left) + [left, (bn + 12)&255, (bn + 12)>>8]
		bn +=1
		yield b

	yield [0x55, 0x55, 0xFE] + [0x00]*128 + [(bn + 12)&255, (bn + 12)>>8]

def generate(fn_xex, fn_wav, patched=False):
	# create the A8 WAV file
	cas=a8cas(fn_wav)

	# read XEX data
	fp=open(fn_xex, "rb")
	xexdata=fp.read()
	fp.close()
	sys.stdout.write("XEX size: %d\n" % len(xexdata))

	# calculate how many sectors and modify the counter (the crc for this sector is ignored)
	a8_sectors = (len(xexdata)+255) / 128
	sys.stdout.write("A8 tape sectors %d\n" % a8_sectors)

	turbo_data.ts_pong[1]['data'][563]=0x6f-(a8_sectors%10)
	a8_sectors /= 10
	turbo_data.ts_pong[1]['data'][562]=0x6f-(a8_sectors%10)
	a8_sectors /= 10
	turbo_data.ts_pong[1]['data'][561]=0x6f-(a8_sectors%10)
	
	# generate the FSK of the TRUBO SOFTWARE header and pong game
        header=turbo_data.ts_header_patched if patched else turbo_data.ts_header
	for i in header: cas.rblock(i['igr'], i['data'])
        if not patched:
	  cas.fsk_falling(4, 6705)
	for i in turbo_data.ts_pong: cas.rblock(i['igr'], i['data'])
	
	# generate the FSK of the XEX dara
	igr=3200
	for b in blocks(xexdata):
		cas.rblock(igr, b+[cas.csum_carry(b)])
		igr=100

	# the tail needed
	cas.fsk_falling(1049, 1341)

	# write the RIFF header
	cas.finalize_wav()
	
if len(sys.argv) > 2:
        patched=False
        o=0
        if sys.argv[1]=="--patched":
            patched=True
            o+=1

	generate(sys.argv[1+o], sys.argv[2+o], patched)
	sys.stdout.write("done!\n")
else:
	sys.stderr.write("usage: %s [--patched] <xexfile> <wavfile>\n" % sys.argv[0])
