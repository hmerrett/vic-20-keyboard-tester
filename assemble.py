#!/usr/bin/env python3
"""
HenryTests VIC-20 Keyboard Matrix Tester - Retro Hardware Discord edition
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
        if name in self.labels:
            raise ValueError(f"Duplicate label '{name}'")
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

    def _abs_l(self, op, lbl, add=0):
        self._e(op, 0, 0)
        self.fixups.append((self.off - 2, lbl, 'word', add))

    def _br(self, op, lbl):
        self._e(op, 0)
        self.fixups.append((self.off - 1, lbl, 'rel', 0))

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
    def sbc_imm(self, v):   self._imm(0xE9, v)
    def and_imm(self, v):   self._imm(0x29, v)
    def ora_imm(self, v):   self._imm(0x09, v)
    def cmp_imm(self, v):   self._imm(0xC9, v)
    def cpx_imm(self, v):   self._imm(0xE0, v)
    def cpy_imm(self, v):   self._imm(0xC0, v)
    def eor_imm(self, v):   self._imm(0x49, v)

    def lda_zp(self, z):    self._zp(0xA5, z)
    def ldx_zp(self, z):    self._zp(0xA6, z)
    def ora_zp(self, z):    self._zp(0x05, z)
    def and_zp(self, z):    self._zp(0x25, z)
    def sta_zp(self, z):    self._zp(0x85, z)
    def stx_zp(self, z):    self._zp(0x86, z)
    def sty_zp(self, z):    self._zp(0x84, z)
    def asl_zp(self, z):    self._zp(0x06, z)
    def lsr_zp(self, z):    self._zp(0x46, z)
    def rol_zp(self, z):    self._zp(0x26, z)
    def inc_zp(self, z):    self._zp(0xE6, z)
    def dec_zp(self, z):    self._zp(0xC6, z)
    def adc_zp(self, z):    self._zp(0x65, z)
    def sta_zpx(self, z):   self._zp(0x95, z)

    def lda_abs(self, a):   self._abs(0xAD, a)
    def sta_abs(self, a):   self._abs(0x8D, a)
    def stx_abs(self, a):   self._abs(0x8E, a)
    def jsr(self, a):       self._abs(0x20, a)
    def jmp(self, a):       self._abs(0x4C, a)

    def sta_absx(self, a):  self._abs(0x9D, a)
    def lda_absx(self, a):  self._abs(0xBD, a)
    def sta_absy(self, a):  self._abs(0x99, a)

    def sta_zpiy(self, z):  self._zpiy(0x91, z)   # STA (zp),Y
    def lda_zpiy(self, z):  self._zpiy(0xB1, z)   # LDA (zp),Y

    def jsr_l(self, lbl):   self._abs_l(0x20, lbl)
    def jmp_l(self, lbl):   self._abs_l(0x4C, lbl)
    def lda_absx_l(self, lbl, add=0): self._abs_l(0xBD, lbl, add)
    def lda_absy_l(self, lbl, add=0): self._abs_l(0xB9, lbl, add)

    def bcc(self, lbl):     self._br(0x90, lbl)
    def bcs(self, lbl):     self._br(0xB0, lbl)
    def beq(self, lbl):     self._br(0xF0, lbl)
    def bne(self, lbl):     self._br(0xD0, lbl)
    def bpl(self, lbl):     self._br(0x10, lbl)

    def byte(self, *bs):
        for b in bs: self._e(b)
    def word_l(self, lbl):
        self._e(0, 0)
        self.fixups.append((self.off - 2, lbl, 'word', 0))

    def resolve(self):
        for (off, lbl, kind, add) in self.fixups:
            addr = self.labels[lbl] + add
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

# VIA #1 — the NMI VIA. The RESTORE key is wired to its CA1 input.
VIA1_PA   = 0x9111     # port A (reading clears the CA1 interrupt flag)
VIA1_PCR  = 0x911C     # peripheral control (CA1 active edge select)
VIA1_IFR  = 0x911D     # interrupt flag register (bit 1 = CA1)
VIA1_IER  = 0x911E     # interrupt enable register
VIA1_PANH = 0x911F     # port A, no handshake (reading leaves the CA1 flag alone)

SCREEN    = 0x1E00     # screen memory (unexpanded)
COLRAM    = 0x9600     # colour RAM
COLOFF    = COLRAM - SCREEN   # colour RAM byte for a cell = screen address + COLOFF
ROW       = 22         # columns per row

# VIC chip
VIC_RASTER = 0x9004    # raster line / 2
VIC_VOICE3 = 0x900C    # soprano voice (bit 7 = on, bits 0-6 = pitch)
VIC_VOLUME = 0x900E    # bits 7-4 aux colour, bits 3-0 volume
VIC_COLOUR = 0x900F    # bits 7-4 background, bit 3 normal video, bits 2-0 border

# Screen origin ($9000/$9001) for each VIC chip, as the stock KERNALs set it.
# Index 0 = NTSC (6560), 1 = PAL (6561).
H_ORIGIN  = [0x05, 0x0C]
V_ORIGIN  = [0x19, 0x26]
PAL_RASTER = 136       # $9004 only gets this high on PAL (312 lines; NTSC has 261)

# Colours
BLACK, WHITE, RED, CYAN, PURPLE, GREEN, BLUE, YELLOW = range(8)
NORMAL_SCREEN = 0x08 | BLUE    # black background, blue border
DONE_SCREEN   = 0x08 | GREEN   # border goes green once every key is tested
VOLUME        = 10

# Zero page
ZP_SL     = 0xFB       # screen pointer low
ZP_SH     = 0xFC       # screen pointer high
ZP_CL     = 0xFD       # colour RAM pointer low (always equal to ZP_SL)
ZP_CH     = 0xFE       # colour RAM pointer high
ZP_ROW    = 0x50       # row data from keyboard (shifted out while drawing)
ZP_COL    = 0x51       # column counter
ZP_MASK   = 0x52       # column select mask
ZP_HIT    = 0x53       # hit flag
ZP_SCODE  = 0x54       # scan code
ZP_TMP    = 0x55
ZP_SEENB  = 0x56       # working copy of this column's "seen" byte
ZP_RSEEN  = 0x57       # RESTORE key "ever pressed" flag
ZP_JSEEN  = 0x58       # joystick "ever pressed" bitmap (b0=U b1=D b2=L b3=F b4=R)
ZP_JNOW   = 0x59       # joystick "pressed now" bitmap (same bit layout)
ZP_ROWC   = 0x5A       # untouched copy of this column's row data
ZP_BITS   = 0x5B       # cell counter
ZP_NEW    = 0x5C       # nonzero if anything was pressed for the first time this frame
ZP_FRAME  = 0x5D       # frame counter
ZP_PHASE  = 0x5E       # rainbow animation phase
ZP_COUNT  = 0x5F       # keys tested so far (0-65)
ZP_DONE   = 0x60       # set once every key has been tested
ZP_TUNE   = 0x61       # position in the tune table (0 = silent)
ZP_FIRST, ZP_LAST = ZP_ROW, ZP_TUNE

# Persistent "ever pressed" bitmap: 8 bytes (one per column), bit set once a
# key has been pressed at least once. Lives in the tape buffer, which is unused
# because we never touch the KERNAL. RAM is random at power-up so it is cleared
# during init.
SEEN      = 0x0340

NUM_KEYS  = 65         # the 64 matrix keys plus RESTORE

# Screen code helpers. Block graphics come from the VIC's built-in character
# set: quadrant/half blocks, and their reversed (+$80) forms.
GLYPHS = {
    '█': 0xA0, '▀': 0xE2, '▄': 0x62, '▌': 0x61,
    '▙': 0xFC, '▛': 0xEC, '▝': 0x7C,
    '●': 0x51, '▒': 0x66,
    '£': 0x1C, '↑': 0x1E, '←': 0x1F,
}

def sc(char):
    """Convert a character to a VIC-20 screen code."""
    if char in GLYPHS:
        return GLYPHS[char]
    c = ord(char)
    if 0x40 <= c <= 0x5F:   # '@', 'A'-'Z', '[' ... '_'
        return c - 0x40
    if 0x20 <= c <= 0x3F:   # space, digits, punctuation
        return c
    raise ValueError(f"No screen code for {char!r}")

def scr(row, col):
    return SCREEN + row * ROW + col

# ====================================================================
# Screen layout
# ====================================================================
# The static parts of the screen are drawn here into a screen image and a
# colour image, which the ROM copies into place at start-up. The main loop then
# only has to update the live parts.
scr_img = bytearray([sc(' ')] * 512)
col_img = bytearray([WHITE] * 512)

def put(row, col, text, colour, reverse=False):
    assert col + len(text) <= ROW, text
    for i, ch in enumerate(text):
        scr_img[row * ROW + col + i] = sc(ch) | (0x80 if reverse else 0)
        col_img[row * ROW + col + i] = colour

# RHD logo (block letters) beside the full community name.
LOGO = ["█▀▙ █ █ █▀▙",
        "█▄▛ █▄█ █ █",
        "█▝▙ █ █ █▄▛"]
LOGO_COL = 1
for r, line in enumerate(LOGO):
    put(r, LOGO_COL, line, RED)             # recoloured every frame
for r, word in enumerate(["RETRO", "HARDWARE", "DISCORD"]):
    put(r, 13, word, WHITE)

STRIPE_ROW = 3
put(STRIPE_ROW, 0, "▀" * ROW, RED)          # rainbow stripe, recoloured every frame
put(4, 0, "VIC-20 KEYBOARD TESTER", CYAN, reverse=True)

# Matrix grid: one screen row per column, "Cn ●●●●●●●● $00".
# Cells run from row bit 7 on the left to bit 0 on the right.
GRID_ROW = 6
LBL_X, CELL_X, HEX_X = 3, 6, 16
put(GRID_ROW - 1, CELL_X, "76543210", PURPLE)
for c in range(8):
    put(GRID_ROW + c, LBL_X, f"C{c}", CYAN)
    put(GRID_ROW + c, CELL_X, "●" * 8, RED)
    put(GRID_ROW + c, HEX_X - 1, "$", PURPLE)
    put(GRID_ROW + c, HEX_X, "00", WHITE)

# Scan code and key name of the first key held down.
SCAN_ROW = 15
put(SCAN_ROW, 1, "SCAN", CYAN)
put(SCAN_ROW, 6, "$", PURPLE)
put(SCAN_ROW, 7, "--", WHITE)
scan_hex = scr(SCAN_ROW, 7)
key_name = scr(SCAN_ROW, 11)

# RESTORE (not part of the matrix; polled separately).
put(16, 1, "RESTORE", CYAN)
put(16, 9, "●", RED)
restore_lbl  = scr(16, 1)
restore_cell = scr(16, 9)

# Joystick as a d-pad, fire in the middle. Each entry:
# (letter, "pressed" bitmask, row, column of the letter). The cell sits
# immediately after its letter; bit layout matches ZP_JNOW/ZP_JSEEN.
put(17, 1, "JOYSTICK", CYAN)
joystick_lbl = scr(17, 1)
joy_dirs = [('U', 0x01, 16, 15), ('D', 0x02, 18, 15), ('L', 0x04, 17, 12),
            ('R', 0x10, 17, 18), ('F', 0x08, 17, 15)]
for letter, mask, r, c in joy_dirs:
    put(r, c, letter, WHITE)
    put(r, c + 1, "●", RED)

# Progress bar and "nn/65" counter.
BAR_ROW, BAR_LEN = 20, 16
put(BAR_ROW, 0, "▒" * BAR_LEN, BLUE)
put(BAR_ROW, 17, "00", WHITE)
put(BAR_ROW, 19, f"/{NUM_KEYS}", PURPLE)
bar = scr(BAR_ROW, 0)
count_digits = scr(BAR_ROW, 17)

# Status line: replaced by DONE_TEXT once every key has been tested.
put(21, 3, "PRESS EVERY KEY", PURPLE)
DONE_TEXT = "ALL KEYS TESTED!"
status = scr(21, 3)

put(22, 4, "BY HENRYTESTS", PURPLE)

# Key names by scan code (column * 8 + row bit), as in the KERNAL's
# keyboard decode table.
KEY_NAMES = [
    "1", "3", "5", "7", "9", "+", "£", "INST/DEL",
    "←", "W", "R", "Y", "I", "P", "*", "RETURN",
    "CTRL", "A", "D", "G", "J", "L", ";", "CRSR L/R",
    "RUN/STOP", "L SHIFT", "X", "V", "N", ",", "/", "CRSR U/D",
    "SPACE", "Z", "C", "B", "M", ".", "R SHIFT", "F1",
    "C=", "S", "F", "H", "K", ":", "=", "F3",
    "Q", "E", "T", "U", "O", "@", "↑", "F5",
    "2", "4", "6", "8", "0", "-", "CLR/HOME", "F7",
]
assert len(KEY_NAMES) == 64 and all(len(n) <= 8 for n in KEY_NAMES)

# Colour cycle for the logo, stripe and "all tested" message (no blue: it is
# too dark on black).
RAINBOW = [RED, RED, PURPLE, PURPLE, CYAN, CYAN, GREEN, GREEN, YELLOW, YELLOW]
BAR_COLOURS = [RED] * 5 + [YELLOW] * 5 + [GREEN] * 6

# Sound: one soprano pitch per frame, 0 = silence. Playback stops on a 0.
TUNE = [0]                                   # idle
BLIP = len(TUNE);   TUNE += [0xEE] * 3 + [0]   # a key's first press
JINGLE = len(TUNE); TUNE += [0xDE] * 5 + [0xE5] * 5 + [0xE9] * 5 + [0xEE] * 12 + [0]

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

# ---- PAL or NTSC? ----
# $9004 holds the raster line / 2, so watch one frame: only a PAL chip ever
# reaches PAL_RASTER before the beam returns to the top.
a.label('tv_top')
a.lda_abs(VIC_RASTER)
a.bne('tv_top')         # wait for the top of a frame...
a.label('tv_leave')
a.lda_abs(VIC_RASTER)
a.beq('tv_leave')       # ...and for the beam to move on
a.ldx_imm(0)            # X = 0: NTSC unless the beam gets far enough
a.label('tv_scan')
a.lda_abs(VIC_RASTER)
a.beq('tv_found')       # back at the top: NTSC
a.cmp_imm(PAL_RASTER)
a.bcc('tv_scan')
a.inx()                 # X = 1: PAL
a.label('tv_found')

# ---- Initialise VIC chip registers ----
a.lda_absx_l('h_origin'); a.sta_abs(0x9000)    # horiz origin for this chip
a.lda_absx_l('v_origin'); a.sta_abs(0x9001)    # vert origin for this chip
a.lda_imm(0x96);  a.sta_abs(0x9002)    # 22 cols + video addr bit
a.lda_imm(0xAE);  a.sta_abs(0x9003)    # 23*2 rows, 8x8 chars
a.lda_imm(0xF0);  a.sta_abs(0x9005)    # screen=$1E00, chars=$8000
a.lda_imm(0x00)
a.sta_abs(0x900A)                       # all voices off
a.sta_abs(0x900B)
a.sta_abs(0x900C)
a.sta_abs(0x900D)
a.lda_imm(VOLUME);        a.sta_abs(VIC_VOLUME)   # aux colour=0
a.lda_imm(NORMAL_SCREEN); a.sta_abs(VIC_COLOUR)

# ---- Copy the screen and colour images into place (512 bytes each) ----
a.ldx_imm(0)
a.label('copy_scr')
a.lda_absx_l('scr_img');        a.sta_absx(SCREEN)
a.lda_absx_l('scr_img', 0x100); a.sta_absx(SCREEN + 0x100)
a.lda_absx_l('col_img');        a.sta_absx(COLRAM)
a.lda_absx_l('col_img', 0x100); a.sta_absx(COLRAM + 0x100)
a.inx()
a.bne('copy_scr')

# ---- Clear the zero page variables and the persistent "seen" bitmap ----
a.lda_imm(0)
a.ldx_imm(ZP_LAST - ZP_FIRST)
a.label('clr_zp')
a.sta_zpx(ZP_FIRST)
a.dex()
a.bpl('clr_zp')
a.ldx_imm(7)
a.label('clr_seen')
a.sta_absx(SEEN)
a.dex()
a.bpl('clr_seen')

# ---- Set up VIA for keyboard scanning ----
a.lda_imm(0xFF);  a.sta_abs(VIA2_DDRB)  # PB = output (columns)
a.lda_imm(0x00);  a.sta_abs(VIA2_DDRA)  # PA = input  (rows)

# ---- Set up VIA #1 for RESTORE polling (no interrupts) ----
a.lda_imm(0x7F);  a.sta_abs(VIA1_IER)   # disable all VIA1 interrupts (no NMI)
a.lda_imm(0x00);  a.sta_abs(VIA1_PCR)   # CA1 active edge = falling (RESTORE down)
a.lda_abs(VIA1_PA)                       # read PA to clear any pending CA1 flag

# ============================================================
# MAIN LOOP - once per frame: scan keyboard and update screen
# ============================================================
a.label('main_loop')

# Wait for the top of the frame. This paces the loop at 50Hz, and the screen
# writes below all land ahead of the beam, so nothing tears.
a.label('vsync')
a.lda_abs(VIC_RASTER)
a.bne('vsync')

# ---- Rainbow animation on the logo and stripe ----
# Stripe column x takes rainbow[x + 3 + phase]; stepping the phase down every
# 8th frame slides the colours to the right. Each logo letter is one solid
# colour, two bands ahead of the stripe beneath it so the two never match.
a.inc_zp(ZP_FRAME)
a.lda_zp(ZP_FRAME)
a.and_imm(0x07)
a.bne('rb_paint')
a.dec_zp(ZP_PHASE)
a.bpl('rb_paint')
a.lda_imm(len(RAINBOW) - 1)
a.sta_zp(ZP_PHASE)
a.label('rb_paint')
a.ldx_zp(ZP_PHASE)
for k in range(3):                      # R, H, D: 3 cells wide, 4 apart
    letter_col = LOGO_COL + 4 * k
    a.lda_absx_l('rainbow', letter_col + STRIPE_ROW + 4)
    for r in range(len(LOGO)):
        for c in range(3):
            a.sta_abs(COLRAM + r * ROW + letter_col + c)
a.ldx_imm(ROW - 1)
a.label('rb_stripe')
a.txa(); a.clc(); a.adc_zp(ZP_PHASE); a.tay()
a.lda_absy_l('rainbow', STRIPE_ROW)
a.sta_absx(COLRAM + STRIPE_ROW * ROW)
a.dex()
a.bpl('rb_stripe')

# ---- Scan the keyboard matrix ----
a.lda_imm(0)
a.sta_zp(ZP_COL)
a.sta_zp(ZP_HIT)
a.sta_zp(ZP_NEW)
a.lda_imm(0xFE)
a.sta_zp(ZP_MASK)

# Point at the first grid row (screen and colour RAM share the low byte)
a.lda_imm(scr(GRID_ROW, 0) & 0xFF)
a.sta_zp(ZP_SL)
a.sta_zp(ZP_CL)
a.lda_imm(scr(GRID_ROW, 0) >> 8)
a.sta_zp(ZP_SH)
a.lda_imm((scr(GRID_ROW, 0) + COLOFF) >> 8)
a.sta_zp(ZP_CH)

a.label('scan_col')

# Drive column
a.lda_zp(ZP_MASK)
a.sta_abs(VIA2_PB)
a.nop(); a.nop(); a.nop(); a.nop()

# Read rows, invert (1 = key pressed)
a.lda_abs(VIA2_PA)
a.eor_imm(0xFF)
a.sta_zp(ZP_ROW)
a.sta_zp(ZP_ROWC)

# Flag any key pressed for the first time (pressed now, not yet seen)
a.ldx_zp(ZP_COL)
a.lda_absx(SEEN)
a.eor_imm(0xFF)
a.and_zp(ZP_ROW)
a.beq('not_new')
a.sta_zp(ZP_NEW)
a.label('not_new')

# Fold this scan's pressed keys into the persistent "seen" bitmap for the
# column, and keep a working copy (ZP_SEENB) for the display loop below.
a.lda_absx(SEEN)
a.ora_zp(ZP_ROW)
a.sta_absx(SEEN)
a.sta_zp(ZP_SEENB)

# The "Cn" label turns green once all 8 keys in the column have been seen
a.ldx_imm(CYAN)
a.cmp_imm(0xFF)
a.bne('col_lbl')
a.ldx_imm(GREEN)
a.label('col_lbl')
a.txa()
a.ldy_imm(LBL_X)
a.sta_zpiy(ZP_CL)
a.iny()
a.sta_zpiy(ZP_CL)

# Write 8 cells to screen at (ZP_SL/SH),Y. For each key:
#   red '●'      never pressed (stays visible until tested)
#   blank        pressed before but released now (checked off)
#   yellow '█'   pressed right now (always wins, so retesting still flags)
a.ldy_imm(CELL_X)
a.lda_imm(8)
a.sta_zp(ZP_BITS)

a.label('bit_lp')
a.ldx_imm(0)        # state 0: never pressed
a.asl_zp(ZP_SEENB)  # C = has this key ever been pressed?
a.bcc('bit_notseen')
a.ldx_imm(1)        # state 1: seen before
a.label('bit_notseen')
a.asl_zp(ZP_ROW)    # C = pressed right now?
a.bcc('put_bit')
a.ldx_imm(2)        # state 2: pressed now (overrides)
a.label('put_bit')
a.lda_absx_l('cell_glyph')
a.sta_zpiy(ZP_SL)
a.lda_absx_l('cell_colour')
a.sta_zpiy(ZP_CL)
a.iny()
a.dec_zp(ZP_BITS)
a.bne('bit_lp')

# Hex value of the row data, after the static '$'
a.ldy_imm(HEX_X)
a.lda_zp(ZP_ROWC)
a.lsr_a(); a.lsr_a(); a.lsr_a(); a.lsr_a()
a.tax()
a.lda_absx_l('hex_tbl')
a.sta_zpiy(ZP_SL)
a.iny()
a.lda_zp(ZP_ROWC)
a.and_imm(0x0F)
a.tax()
a.lda_absx_l('hex_tbl')
a.sta_zpiy(ZP_SL)

# ---- Scan code of the first pressed key ----
a.lda_zp(ZP_HIT)
a.bne('no_key')     # already found one in an earlier column
a.lda_zp(ZP_ROWC)
a.beq('no_key')
a.ldy_imm(0)
a.label('fbit')
a.lsr_a()
a.bcs('fkey')
a.iny()
a.bne('fbit')       # always taken: A has a bit set

a.label('fkey')
a.sty_zp(ZP_TMP)
a.lda_zp(ZP_COL)
a.asl_a(); a.asl_a(); a.asl_a()
a.ora_zp(ZP_TMP)
a.sta_zp(ZP_SCODE)
a.inc_zp(ZP_HIT)

a.label('no_key')

# Advance both pointers by 22 (one row)
a.clc()
a.lda_zp(ZP_SL)
a.adc_imm(ROW)
a.sta_zp(ZP_SL)
a.sta_zp(ZP_CL)
a.bcc('no_carry')
a.inc_zp(ZP_SH)
a.inc_zp(ZP_CH)
a.label('no_carry')

# Next column
a.sec(); a.rol_zp(ZP_MASK)
a.inc_zp(ZP_COL)
a.lda_zp(ZP_COL)
a.cmp_imm(8)
a.beq('cols_done')
a.jmp_l('scan_col')
a.label('cols_done')

# ---- Scan code and key name readout ----
a.lda_zp(ZP_HIT)
a.beq('show_none')

a.lda_zp(ZP_SCODE)
a.lsr_a(); a.lsr_a(); a.lsr_a(); a.lsr_a()
a.tax()
a.lda_absx_l('hex_tbl')
a.sta_abs(scan_hex)
a.lda_zp(ZP_SCODE)
a.and_imm(0x0F)
a.tax()
a.lda_absx_l('hex_tbl')
a.sta_abs(scan_hex + 1)

a.ldx_zp(ZP_SCODE)
for i in range(8):
    a.lda_absx_l(f'key_name{i}')
    a.sta_abs(key_name + i)
a.jmp_l('restore_chk')

a.label('show_none')
a.lda_imm(sc('-'))
a.sta_abs(scan_hex)
a.sta_abs(scan_hex + 1)
a.lda_imm(sc(' '))
for i in range(8):
    a.sta_abs(key_name + i)

def show_state(cell, label, label_len, label_colours):
    """Draw a cell for the state in X (0 never, 1 seen, 2 pressed now), and
    colour its label: normal until tested, then green."""
    a.lda_absx_l('cell_glyph')
    a.sta_abs(cell)
    a.lda_absx_l('cell_colour')
    a.sta_abs(cell + COLOFF)
    a.lda_absx_l(label_colours)
    for i in range(label_len):
        a.sta_abs(label + COLOFF + i)

# ---- Poll RESTORE (VIA #1 CA1 edge) ----
# Edge-latched: a set CA1 flag means RESTORE was pressed since the last poll.
a.label('restore_chk')
a.ldx_imm(0)
a.lda_abs(VIA1_IFR)
a.and_imm(0x02)         # CA1 flag
a.beq('rest_no_edge')
a.lda_abs(VIA1_PA)      # read PA to clear the CA1 flag (re-arm for next press)
a.lda_zp(ZP_RSEEN)
a.bne('rest_now')
a.lda_imm(1)            # first press
a.sta_zp(ZP_NEW)
a.sta_zp(ZP_RSEEN)
a.label('rest_now')
a.ldx_imm(2)
a.bne('rest_show')      # always taken
a.label('rest_no_edge')
a.lda_zp(ZP_RSEEN)
a.beq('rest_show')
a.ldx_imm(1)
a.label('rest_show')
show_state(restore_cell, restore_lbl, len("RESTORE"), 'label_cyan')

# ---- Read joystick (VIA1 PA bits 2-5 + VIA2 PB7) ----
# Build ZP_JNOW with pressed=1: b0=Up b1=Down b2=Left b3=Fire b4=Right.
# Read port A without handshake so a RESTORE edge arriving now isn't lost.
a.lda_abs(VIA1_PANH)    # Up/Down/Left/Fire are PA bits 2-5, active low
a.eor_imm(0xFF)         # pressed = 1
a.lsr_a(); a.lsr_a()    # shift bits 2-5 down to bits 0-3
a.and_imm(0x0F)         # b0=Up b1=Down b2=Left b3=Fire
a.sta_zp(ZP_JNOW)
# Right is on VIA2 PB7, which is normally a keyboard column output. Drive it
# high first so the line isn't still low when it becomes an input.
a.lda_imm(0xFF); a.sta_abs(VIA2_PB)
a.lda_imm(0x7F); a.sta_abs(VIA2_DDRB)   # make PB7 an input
a.lda_abs(VIA2_PB)
a.eor_imm(0xFF)         # pressed = 1
a.and_imm(0x80)         # keep bit 7 (Right)
a.lsr_a(); a.lsr_a(); a.lsr_a()         # bit7 -> bit4 ($80 -> $10)
a.ora_zp(ZP_JNOW)
a.sta_zp(ZP_JNOW)
a.lda_imm(0xFF); a.sta_abs(VIA2_DDRB)   # restore all columns to output
# Flag first presses, then fold into the persistent joystick "seen" bitmap.
a.lda_zp(ZP_JSEEN); a.eor_imm(0xFF); a.and_zp(ZP_JNOW)
a.beq('j_not_new')
a.sta_zp(ZP_NEW)
a.label('j_not_new')
a.lda_zp(ZP_JSEEN); a.ora_zp(ZP_JNOW); a.sta_zp(ZP_JSEEN)

for idx, (letter, mask, r, c) in enumerate(joy_dirs):
    a.ldx_imm(0)
    a.lda_zp(ZP_JSEEN); a.and_imm(mask)
    a.beq(f'j_notseen{idx}')
    a.ldx_imm(1)
    a.label(f'j_notseen{idx}')
    a.lda_zp(ZP_JNOW); a.and_imm(mask)
    a.beq(f'j_show{idx}')
    a.ldx_imm(2)
    a.label(f'j_show{idx}')
    show_state(scr(r, c + 1), scr(r, c), 1, 'label_white')

# "JOYSTICK" turns green once all five inputs have been seen
a.ldx_imm(0)
a.lda_zp(ZP_JSEEN)
a.cmp_imm(0x1F)
a.bne('j_lbl')
a.ldx_imm(1)
a.label('j_lbl')
a.lda_absx_l('label_cyan')
for i in range(len("JOYSTICK")):
    a.sta_abs(joystick_lbl + COLOFF + i)

# ---- Count tested keys: set bits in SEEN, plus RESTORE ----
a.lda_imm(0)
a.sta_zp(ZP_COUNT)
a.ldx_imm(7)
a.label('cnt_col')
a.lda_absx(SEEN)
a.label('cnt_bit')
a.lsr_a()           # C = key seen, Z = no more bits in this column
a.bcc('cnt_next')
a.inc_zp(ZP_COUNT)
a.cmp_imm(0)        # restore Z for A
a.label('cnt_next')
a.bne('cnt_bit')
a.dex()
a.bpl('cnt_col')
a.lda_zp(ZP_RSEEN)
a.beq('cnt_show')
a.inc_zp(ZP_COUNT)

# Two decimal digits
a.label('cnt_show')
a.lda_zp(ZP_COUNT)
a.ldx_imm(sc('0'))
a.label('cnt_tens')
a.cmp_imm(10)
a.bcc('cnt_ones')
a.sbc_imm(10)       # carry is set by the compare
a.inx()
a.bne('cnt_tens')   # always taken
a.label('cnt_ones')
a.stx_abs(count_digits)
a.ora_imm(sc('0'))
a.sta_abs(count_digits + 1)

# ---- Progress bar: bar_len[count] half-cells, coloured by position ----
a.ldx_zp(ZP_COUNT)
a.lda_absx_l('bar_len')
a.sta_zp(ZP_TMP)    # half-cells still to draw
a.ldx_imm(0)
a.label('bar_lp')
a.lda_zp(ZP_TMP)
a.beq('bar_empty')
a.dec_zp(ZP_TMP)
a.beq('bar_half')
a.dec_zp(ZP_TMP)
a.lda_imm(sc('█'))
a.bne('bar_fill')   # always taken
a.label('bar_half')
a.lda_imm(sc('▌'))
a.label('bar_fill')
a.sta_absx(bar)
a.lda_absx_l('bar_colour')
a.bne('bar_col')    # always taken: no black in the table
a.label('bar_empty')
a.lda_imm(sc('▒'))
a.sta_absx(bar)
a.lda_imm(BLUE)
a.label('bar_col')
a.sta_absx(bar + COLOFF)
a.inx()
a.cpx_imm(BAR_LEN)
a.bne('bar_lp')

# ---- Sound cue for a first press ----
a.lda_zp(ZP_NEW)
a.beq('no_blip')
a.lda_imm(BLIP)
a.sta_zp(ZP_TUNE)
a.label('no_blip')

# ---- All keys tested: jingle, green border, rainbow message ----
a.lda_zp(ZP_COUNT)
a.cmp_imm(NUM_KEYS)
a.bne('not_done')
a.lda_zp(ZP_DONE)
a.bne('done_msg')
a.inc_zp(ZP_DONE)
a.lda_imm(JINGLE)
a.sta_zp(ZP_TUNE)
a.lda_imm(DONE_SCREEN)
a.sta_abs(VIC_COLOUR)
a.label('done_msg')
a.ldx_imm(len(DONE_TEXT) - 1)
a.label('done_lp')
a.lda_absx_l('done_txt')
a.sta_absx(status)
a.txa(); a.clc(); a.adc_zp(ZP_PHASE); a.tay()
a.lda_absy_l('rainbow')
a.sta_absx(status + COLOFF)
a.dex()
a.bpl('done_lp')
a.label('not_done')

# ---- Play the current tune, one table entry per frame ----
a.ldx_zp(ZP_TUNE)
a.lda_absx_l('tune')
a.sta_abs(VIC_VOICE3)
a.beq('tune_idle')  # parked on a 0: silence
a.inc_zp(ZP_TUNE)
a.label('tune_idle')

a.jmp_l('main_loop')

# ============================================================
# Data tables
# ============================================================
a.label('h_origin'); a.byte(*H_ORIGIN)
a.label('v_origin'); a.byte(*V_ORIGIN)

a.label('hex_tbl')
# Screen codes for '0'-'9','A'-'F'
for c in '0123456789ABCDEF':
    a.byte(sc(c))

# Indexed by state: never pressed, seen, pressed now
a.label('cell_glyph');  a.byte(sc('●'), sc(' '), sc('█'))
a.label('cell_colour'); a.byte(RED, WHITE, YELLOW)
a.label('label_cyan');  a.byte(CYAN, GREEN, GREEN)
a.label('label_white'); a.byte(WHITE, GREEN, GREEN)

# Long enough for the largest col + row + phase index
a.label('rainbow')
for i in range(ROW + STRIPE_ROW + len(RAINBOW)):
    a.byte(RAINBOW[i % len(RAINBOW)])

a.label('bar_colour')
a.byte(*BAR_COLOURS)

# Half-cells of progress bar to fill for each count (full only at NUM_KEYS)
a.label('bar_len')
for n in range(NUM_KEYS + 1):
    a.byte(n * 2 * BAR_LEN // NUM_KEYS)

a.label('tune')
a.byte(*TUNE)

a.label('done_txt')
a.byte(*[sc(c) for c in DONE_TEXT])

# Key names, one 64-byte table per character position
for i in range(8):
    a.label(f'key_name{i}')
    a.byte(*[sc(name.ljust(8)[i]) for name in KEY_NAMES])

a.label('scr_img')
a.byte(*scr_img)
a.label('col_img')
a.byte(*col_img)

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
