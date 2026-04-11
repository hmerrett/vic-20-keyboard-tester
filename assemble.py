#!/usr/bin/env python3
"""
HenryTests VIC-20 Keyboard Matrix Tester
Writes directly to VIC chip registers and screen memory.
No CHROUT, no KERNAL init, no dependency on anything except hardware.
Output: kbtest.bin (8192 bytes, $A000-$BFFF)
"""

class Asm6502:
    def __init__(self, origin, size, fill=0xFF):
        self.origin = origin
        self.rom = bytearray([fill] * size)
        self.pc = origin
        self.labels = {}
        self.fixups = []

    @property
    def off(self):
        return self.pc - self.origin

    def label(self, name):
        self.labels[name] = self.pc

    def _e(self, *bs):
        for b in bs:
            self.rom[self.off] = b & 0xFF
            self.pc += 1

    def _imp(self, op):         self._e(op)
    def _imm(self, op, v):      self._e(op, v & 0xFF)
    def _zp(self, op, z):       self._e(op, z & 0xFF)
    def _abs(self, op, a):      self._e(op, a & 0xFF, (a >> 8) & 0xFF)
    def _zpiy(self, op, z):     self._e(op, z & 0xFF)          # (zp),Y

    def _abs_l(self, op, lbl):
        self._e(op, 0, 0)
        self.fixups.append((self.off - 2, lbl, 'word'))

    def _br(self, op, lbl):
        self._e(op, 0)
        self.fixups.append((self.off - 1, lbl, 'rel'))

    # Instructions
    def nop(self):          self._imp(0xEA)
    def sei(self):          self._imp(0x78)
    def cli(self):          self._imp(0x58)
    def cld(self):          self._imp(0xD8)
    def clc(self):          self._imp(0x18)
    def sec(self):          self._imp(0x38)
    def pha(self):          self._imp(0x48)
    def pla(self):          self._imp(0x68)
    def rts(self):          self._imp(0x60)
    def inx(self):          self._imp(0xE8)
    def iny(self):          self._imp(0xC8)
    def dex(self):          self._imp(0xCA)
    def dey(self):          self._imp(0x88)
    def tax(self):          self._imp(0xAA)
    def tay(self):          self._imp(0xA8)
    def txa(self):          self._imp(0x8A)
    def tya(self):          self._imp(0x98)
    def txs(self):          self._imp(0x9A)
    def asl_a(self):        self._imp(0x0A)
    def lsr_a(self):        self._imp(0x4A)

    def lda_imm(self, v):   self._imm(0xA9, v)
    def ldx_imm(self, v):   self._imm(0xA2, v)
    def ldy_imm(self, v):   self._imm(0xA0, v)
    def adc_imm(self, v):   self._imm(0x69, v)
    def and_imm(self, v):   self._imm(0x29, v)
    def ora_imm(self, v):   self._imm(0x09, v)
    def cmp_imm(self, v):   self._imm(0xC9, v)
    def cpx_imm(self, v):   self._imm(0xE0, v)
    def cpy_imm(self, v):   self._imm(0xC0, v)
    def eor_imm(self, v):   self._imm(0x49, v)

    def lda_zp(self, z):    self._zp(0xA5, z)
    def sta_zp(self, z):    self._zp(0x85, z)
    def stx_zp(self, z):    self._zp(0x86, z)
    def sty_zp(self, z):    self._zp(0x84, z)
    def asl_zp(self, z):    self._zp(0x06, z)
    def lsr_zp(self, z):    self._zp(0x46, z)
    def rol_zp(self, z):    self._zp(0x26, z)
    def inc_zp(self, z):    self._zp(0xE6, z)
    def dec_zp(self, z):    self._zp(0xC6, z)
    def adc_zp(self, z):    self._zp(0x65, z)

    def lda_abs(self, a):   self._abs(0xAD, a)
    def sta_abs(self, a):   self._abs(0x8D, a)
    def jsr(self, a):       self._abs(0x20, a)
    def jmp(self, a):       self._abs(0x4C, a)

    def sta_absx(self, a):  self._abs(0x9D, a)
    def lda_absx(self, a):  self._abs(0xBD, a)

    def sta_zpiy(self, z):  self._zpiy(0x91, z)   # STA (zp),Y
    def lda_zpiy(self, z):  self._zpiy(0xB1, z)   # LDA (zp),Y

    def jsr_l(self, lbl):   self._abs_l(0x20, lbl)
    def jmp_l(self, lbl):   self._abs_l(0x4C, lbl)
    def lda_absx_l(self, lbl): self._abs_l(0xBD, lbl)

    def bcc(self, lbl):     self._br(0x90, lbl)
    def bcs(self, lbl):     self._br(0xB0, lbl)
    def beq(self, lbl):     self._br(0xF0, lbl)
    def bne(self, lbl):     self._br(0xD0, lbl)
    def bpl(self, lbl):     self._br(0x10, lbl)

    def byte(self, *bs):
        for b in bs: self._e(b)
    def word_l(self, lbl):
        self._e(0, 0)
        self.fixups.append((self.off - 2, lbl, 'word'))
    def string(self, s):
        for c in s: self._e(ord(c))

    def resolve(self):
        for (off, lbl, kind) in self.fixups:
            addr = self.labels[lbl]
            if kind == 'word':
                self.rom[off]     = addr & 0xFF
                self.rom[off + 1] = (addr >> 8) & 0xFF
            elif kind == 'rel':
                base = self.origin + off + 1
                delta = addr - base
                if not (-128 <= delta <= 127):
                    raise ValueError(f"Branch '{lbl}' out of range: {delta}")
                self.rom[off] = delta & 0xFF

    def save(self, fn):
        self.resolve()
        with open(fn, 'wb') as f:
            f.write(self.rom)


# ====================================================================
# Hardware equates
# ====================================================================
VIA2_PB   = 0x9120
VIA2_PA   = 0x9121
VIA2_DDRB = 0x9122
VIA2_DDRA = 0x9123

SCREEN    = 0x1E00     # screen memory (unexpanded)
COLRAM    = 0x9600     # colour RAM
ROW       = 22         # columns per row

# VIC chip
VIC_BASE  = 0x9000

# Zero page
ZP_SL     = 0xFB       # screen pointer low
ZP_SH     = 0xFC       # screen pointer high
ZP_ROW    = 0xFD       # row data from keyboard
ZP_COL    = 0xFE       # column counter
ZP_MASK   = 0x50       # column select mask
ZP_HIT    = 0x51       # hit flag
ZP_SCODE  = 0x52       # scan code
ZP_TMP    = 0x53

# Screen code helpers
def sc(char):
    """Convert ASCII char to VIC-20 screen code."""
    c = ord(char) if isinstance(char, str) else char
    if 0x41 <= c <= 0x5A:   # 'A'-'Z'
        return c - 0x40
    elif 0x30 <= c <= 0x39: # '0'-'9'
        return c
    elif c == 0x20: return 0x20  # space
    elif c == ord('-'): return 0x2D
    elif c == ord('.'): return 0x2E
    elif c == ord('*'): return 0x2A
    elif c == ord(':'): return 0x1B
    elif c == ord('$'): return 0x24
    elif c == ord(' '): return 0x20
    else: return 0x20

# ====================================================================
# Build
# ====================================================================
a = Asm6502(origin=0xA000, size=8192, fill=0xFF)

# ---- Cartridge header ----
a.word_l('entry')
a.word_l('entry')
a.byte(0x41, 0x30, 0xC3, 0xC2, 0xCD)   # "A0CBM"

# ---- Entry: fully standalone, no KERNAL ----
a.label('entry')
a.sei()
a.cld()
a.ldx_imm(0xFF)
a.txs()

# ---- Initialise VIC chip registers ----
# PAL values
a.lda_imm(0x0C);  a.sta_abs(0x9000)    # horiz origin (PAL)
a.lda_imm(0x26);  a.sta_abs(0x9001)    # vert origin  (PAL)
a.lda_imm(0x96);  a.sta_abs(0x9002)    # 22 cols + video addr bit
a.lda_imm(0xAE);  a.sta_abs(0x9003)    # 23*2 rows, 8x8 chars
a.lda_imm(0xF0);  a.sta_abs(0x9005)    # screen=$1E00, chars=$8000
a.lda_imm(0x00)
a.sta_abs(0x900A)                       # sound off
a.sta_abs(0x900B)
a.sta_abs(0x900C)
a.sta_abs(0x900D)
a.sta_abs(0x900E)                       # aux colour=0, vol=0
a.lda_imm(0x1B);  a.sta_abs(0x900F)    # bg=white, border=cyan

# ---- Clear screen with spaces ----
a.lda_imm(0x20)                         # space screen code
a.ldx_imm(0)
a.label('clr')
a.sta_absx(SCREEN)
a.sta_absx(SCREEN + 0x100)
a.dex()
a.bne('clr')

# ---- Fill colour RAM with blue (6) ----
a.lda_imm(0x06)
a.ldx_imm(0)
a.label('clr_col')
a.sta_absx(COLRAM)
a.sta_absx(COLRAM + 0x100)
a.dex()
a.bne('clr_col')

# ---- Write title to screen memory ----
title_text = "HENRYTESTS"
for i, ch in enumerate(title_text):
    a.lda_imm(sc(ch))
    a.sta_abs(SCREEN + i)

subtitle = "KEYBOARD TESTER"
for i, ch in enumerate(subtitle):
    a.lda_imm(sc(ch))
    a.sta_abs(SCREEN + ROW + i)

subtitle2 = "PRESS KEYS..."
for i, ch in enumerate(subtitle2):
    a.lda_imm(sc(ch))
    a.sta_abs(SCREEN + 2 * ROW + i)

# ---- Write static labels for 8 columns ----
# Row 3 onwards: "C0 " "C1 " ... "C7 "
for col in range(8):
    base = SCREEN + (3 + col) * ROW
    a.lda_imm(sc('C'))
    a.sta_abs(base)
    a.lda_imm(sc(str(col)))
    a.sta_abs(base + 1)
    a.lda_imm(0x20)         # space
    a.sta_abs(base + 2)

# Write "SCAN:" label on row 12
scan_row = SCREEN + 12 * ROW
scan_text = "SCAN:"
for i, ch in enumerate(scan_text):
    a.lda_imm(sc(ch))
    a.sta_abs(scan_row + i)

# ---- Set up VIA for keyboard scanning ----
a.lda_imm(0xFF);  a.sta_abs(VIA2_DDRB)  # PB = output (columns)
a.lda_imm(0x00);  a.sta_abs(VIA2_DDRA)  # PA = input  (rows)

# ============================================================
# MAIN LOOP - scan keyboard and update screen directly
# ============================================================
a.label('main_loop')

a.lda_imm(0)
a.sta_zp(ZP_COL)
a.sta_zp(ZP_HIT)
a.lda_imm(0xFE)
a.sta_zp(ZP_MASK)

# Set screen pointer to row 3, column 3 (after "Cn ")
a.lda_imm((SCREEN + 3 * ROW + 3) & 0xFF)
a.sta_zp(ZP_SL)
a.lda_imm((SCREEN + 3 * ROW + 3) >> 8)
a.sta_zp(ZP_SH)

a.label('scan_col')

# Drive column
a.lda_zp(ZP_MASK)
a.sta_abs(VIA2_PB)
a.nop(); a.nop(); a.nop(); a.nop()

# Read rows, invert
a.lda_abs(VIA2_PA)
a.eor_imm(0xFF)
a.sta_zp(ZP_ROW)

# Write 8 dots/stars to screen at (ZP_SL/SH),Y
a.ldy_imm(0)       # Y = offset within row (starting at col 3)
a.ldx_imm(8)       # bit counter

a.label('bit_lp')
a.asl_zp(ZP_ROW)
a.lda_imm(0x2E)    # '.' screen code
a.bcc('put_bit')
a.lda_imm(0x2A)    # '*' screen code
a.label('put_bit')
a.sta_zpiy(ZP_SL)  # STA (ZP_SL),Y
a.iny()
a.dex()
a.bne('bit_lp')

# Write " $" after the 8 bits (Y is now 8)
a.lda_imm(0x20)    # space
a.sta_zpiy(ZP_SL)
a.iny()             # Y=9
a.lda_imm(0x24)    # '$'
a.sta_zpiy(ZP_SL)
a.iny()             # Y=10

# Write hex value of row data
# Re-read the row
a.lda_zp(ZP_MASK)
a.sta_abs(VIA2_PB)
a.nop(); a.nop()
a.lda_abs(VIA2_PA)
a.eor_imm(0xFF)
a.sta_zp(ZP_TMP)

# High nybble
a.lsr_a(); a.lsr_a(); a.lsr_a(); a.lsr_a()
a.tax()
a.lda_absx_l('hex_tbl')
a.sta_zpiy(ZP_SL)
a.iny()             # Y=11

# Low nybble
a.lda_zp(ZP_TMP)
a.and_imm(0x0F)
a.tax()
a.lda_absx_l('hex_tbl')
a.sta_zpiy(ZP_SL)

# ---- Check for pressed key, compute scan code ----
a.lda_zp(ZP_MASK)
a.sta_abs(VIA2_PB)
a.nop(); a.nop()
a.lda_abs(VIA2_PA)
a.eor_imm(0xFF)
a.beq('no_key')

a.sta_zp(ZP_TMP)
a.ldy_imm(0)
a.label('fbit')
a.lsr_zp(ZP_TMP)
a.bcs('fkey')
a.iny()
a.cpy_imm(8)
a.bne('fbit')
a.beq('no_key')

a.label('fkey')
a.lda_zp(ZP_COL)
a.asl_a(); a.asl_a(); a.asl_a()
a.sty_zp(ZP_TMP)
a.clc(); a.adc_zp(ZP_TMP)
a.sta_zp(ZP_SCODE)
a.lda_imm(1); a.sta_zp(ZP_HIT)

a.label('no_key')

# Advance screen pointer by 22 (one row)
a.clc()
a.lda_zp(ZP_SL)
a.adc_imm(ROW)
a.sta_zp(ZP_SL)
a.lda_zp(ZP_SH)
a.adc_imm(0)
a.sta_zp(ZP_SH)

# Next column
a.sec(); a.rol_zp(ZP_MASK)
a.inc_zp(ZP_COL)
a.lda_zp(ZP_COL)
a.cmp_imm(8)
a.beq('cols_done')
a.jmp_l('scan_col')
a.label('cols_done')

# ---- Update scan code display on row 12 ----
scan_val_addr = SCREEN + 12 * ROW + 6   # after "SCAN: "

a.lda_zp(ZP_HIT)
a.beq('show_none')

# Show hex scan code
a.lda_zp(ZP_SCODE)
a.lsr_a(); a.lsr_a(); a.lsr_a(); a.lsr_a()
a.tax()
a.lda_absx_l('hex_tbl')
a.sta_abs(scan_val_addr)

a.lda_zp(ZP_SCODE)
a.and_imm(0x0F)
a.tax()
a.lda_absx_l('hex_tbl')
a.sta_abs(scan_val_addr + 1)

a.lda_imm(0x20)
a.sta_abs(scan_val_addr + 2)
a.jmp_l('scan_delay')

a.label('show_none')
a.lda_imm(0x2D)     # '-'
a.sta_abs(scan_val_addr)
a.sta_abs(scan_val_addr + 1)
a.lda_imm(0x20)
a.sta_abs(scan_val_addr + 2)

a.label('scan_delay')
# Brief delay
a.ldx_imm(4)
a.label('dly_o')
a.ldy_imm(0)
a.label('dly_i')
a.nop(); a.nop()
a.dey(); a.bne('dly_i')
a.dex(); a.bne('dly_o')

a.jmp_l('main_loop')

# ============================================================
# Data tables
# ============================================================
a.label('hex_tbl')
# Screen codes for '0'-'9','A'-'F'
for c in '0123456789':
    a.byte(sc(c))
for c in 'ABCDEF':
    a.byte(sc(c))

# ============================================================
# Done
# ============================================================
end = a.pc
used = end - a.origin
print(f"Code:  ${a.origin:04X}-${end-1:04X}  ({used} bytes)")
print(f"ROM:   $A000-$BFFF  (8192 bytes)")
print(f"Free:  {8192 - used} bytes")

a.save("kbtest.bin")
print("Written: kbtest.bin")

# Also write .prg version (with 2-byte load address header) for VICE
with open("kbtest.prg", "wb") as f:
    f.write(bytes([0x00, 0xA0]))  # load address $A000
    f.write(a.rom)
print("Written: kbtest.prg (with $A000 load address header for VICE)")

# Intel HEX
lines = []
for i in range(0, len(a.rom), 16):
    chunk = a.rom[i:i+16]
    rec = [len(chunk), (i >> 8) & 0xFF, i & 0xFF, 0x00] + list(chunk)
    cksum = (~sum(rec) + 1) & 0xFF
    lines.append(':' + ''.join(f'{b:02X}' for b in rec) + f'{cksum:02X}')
lines.append(':00000001FF')
with open("kbtest.hex", 'w') as f:
    f.write('\n'.join(lines) + '\n')
print("Written: kbtest.hex")
