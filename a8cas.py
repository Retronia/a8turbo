import sys
import math
import struct

class a8cas:
	conf_sampling = None
	conf_baud = None
	conf_bits = None
	conf_amp = None
	conf_space = None
	conf_mark = None
	
	space_mark = None
	bit_len = None

	pos = 0.0
	pos_bit = 0.0
	csamples = 0

	f=None
	
	def __init__(self, filename, sampling = 44100, baud = 600, bits = 16, amp = (2**15) * 0.8, space = 3995, mark = 5327):
		self.conf_sampling = sampling
		self.conf_baud = baud
		self.conf_bits = bits
		self.conf_amp = amp
		self.conf_space = space
		self.conf_mark = mark
		
		self.space_mark = (math.pi * 2 * self.conf_space / self.conf_sampling, math.pi * 2 * self.conf_mark / self.conf_sampling)
		self.bit_len = self.conf_sampling / float(self.conf_baud)

		self.f = open(filename, "wb")
		self.f.seek(44)
		
	def csum_carry(self, d):
		c, r = 0, 0
		for v in d:
			r += v+c
			c = (r>>8)&1
			r = r&255
		return r
	
	def osc_write(self, samples, inc):
		for i in range(samples):
			self.csamples += 1
			yield math.sin(self.pos) * self.conf_amp
			self.pos += inc
			self.pos = self.pos % (math.pi * 2)

	def byte(self, b):
		b = (b << 1) | 0x200
		
		for i in range(10):
			r = int(round(self.bit_len + self.pos_bit))
			self.f.write(struct.pack("<%dh" % r, *self.osc_write(r, self.space_mark[b&1])))
			self.pos_bit += self.bit_len - r
			b = b >> 1
		
	def rblock(self, igr, data):
		s =  int(round(self.conf_sampling * (igr / 1000.0)))
		self.f.write(struct.pack("<%dh" % s, *self.osc_write(s, self.space_mark[1])))
		for b in data: self.byte(b)

	def fsk_falling(self, mark, space):
		s=int(round(self.conf_sampling * (mark / 1000.0)))
		self.f.write(struct.pack("<%dh" % s, *self.osc_write(s, self.space_mark[1])))
		s=int(round(self.conf_sampling * (space / 10000.0)))
		self.f.write(struct.pack("<%dh" % s, *self.osc_write(s, self.space_mark[0])))	

	def finalize_wav(self):
		self.f.seek(0)
		
		schunk2_size=self.csamples*2
		schunk1_size=16
		chunk_size=schunk2_size+36
		self.f.write(struct.pack("<4sI4s", "RIFF", chunk_size, "WAVE"))
		self.f.write(struct.pack("<4sIHHIIHH", "fmt ", schunk1_size, 1, 1, self.conf_sampling, self.conf_sampling*2, 2, 16))
		self.f.write(struct.pack("<4sI", "data", schunk2_size))

		self.f.close()		
